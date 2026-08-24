// Package router is the live deployment registry (litellm.Router).
package router

import (
	"crypto/rand"
	"encoding/base64"
	"strings"
	"sync"
	"time"

	"github.com/noizu-labs/go-litellm/internal/config"
	"github.com/noizu-labs/go-litellm/internal/jsonx"
)

// Router holds the mutable model list and selects deployments.
type Router struct {
	mu          sync.RWMutex
	deployments []map[string]any
	cfg         *config.Config
	cooldowns   *CooldownCache
}

// New seeds from config.model_list.
func New(cfg *config.Config) *Router {
	r := &Router{cfg: cfg, cooldowns: NewCooldownCache()}
	if cfg != nil {
		for _, d := range cfg.SnapshotModelList() {
			r.deployments = append(r.deployments, ensureID(jsonx.Clone(d)))
		}
	}
	return r
}

// Deployments returns a snapshot of the registry.
func (r *Router) Deployments() []map[string]any {
	r.mu.RLock()
	defer r.mu.RUnlock()
	out := make([]map[string]any, len(r.deployments))
	copy(out, r.deployments)
	return out
}

// Group returns deployments whose model_name matches (after alias resolution).
func (r *Router) Group(modelName string) []map[string]any {
	resolved := r.resolveAlias(modelName)
	var out []map[string]any
	for _, d := range r.Deployments() {
		if jsonx.Str(d, "model_name") == resolved {
			out = append(out, d)
		}
	}
	return out
}

// ModelNames returns distinct visible model_names.
func (r *Router) ModelNames() []string {
	seen := map[string]bool{}
	var out []string
	for _, d := range r.Deployments() {
		name := jsonx.Str(d, "model_name")
		if name == "" || seen[name] {
			continue
		}
		seen[name] = true
		out = append(out, name)
	}
	return out
}

// Select picks one deployment for a requested model.
func (r *Router) Select(modelName string) (map[string]any, bool) {
	candidates := r.Group(modelName)
	if len(candidates) == 0 {
		return nil, false
	}
	var available []map[string]any
	for _, d := range candidates {
		if !r.cooldowns.CooledDown(jsonx.Str(d, "model_id")) {
			available = append(available, d)
		}
	}
	pool := available
	if len(pool) == 0 {
		pool = candidates
	}
	return Pick(r.strategy(), pool), true
}

// Lookup is Select that returns nil when missing.
func (r *Router) Lookup(modelName string) map[string]any {
	d, ok := r.Select(modelName)
	if ok {
		return d
	}
	// Claude Code v2.1.116+ appends "[1m]"; groq-pro used to miss those aliases.
	if strings.HasSuffix(modelName, "[1m]") {
		if d, ok = r.Select(strings.TrimSuffix(modelName, "[1m]")); ok {
			return d
		}
	}
	return nil
}

// Add registers a deployment and assigns a model_id if absent.
func (r *Router) Add(deployment map[string]any) map[string]any {
	stored := ensureID(jsonx.Clone(deployment))
	if _, ok := stored["litellm_params"]; !ok {
		stored["litellm_params"] = map[string]any{}
	}
	if _, ok := stored["model_info"]; !ok {
		stored["model_info"] = map[string]any{}
	}
	r.mu.Lock()
	r.deployments = append(r.deployments, stored)
	r.mu.Unlock()
	return stored
}

// Delete removes a deployment by model_id.
func (r *Router) Delete(modelID string) bool {
	r.mu.Lock()
	defer r.mu.Unlock()
	kept := r.deployments[:0]
	found := false
	for _, d := range r.deployments {
		if jsonx.Str(d, "model_id") == modelID {
			found = true
			continue
		}
		kept = append(kept, d)
	}
	if !found {
		return false
	}
	// re-slice into a new backing array so we don't leak the last elem
	out := make([]map[string]any, len(kept))
	copy(out, kept)
	r.deployments = out
	return true
}

// Update merges changes into a deployment by model_id.
func (r *Router) Update(modelID string, changes map[string]any) (map[string]any, bool) {
	r.mu.Lock()
	defer r.mu.Unlock()
	for i, d := range r.deployments {
		if jsonx.Str(d, "model_id") != modelID {
			continue
		}
		updated := jsonx.DeepMerge(d, changes)
		r.deployments[i] = updated
		return updated, true
	}
	return nil, false
}

// Set replaces the entire deployment set.
func (r *Router) Set(list []map[string]any) {
	seed := make([]map[string]any, 0, len(list))
	for _, d := range list {
		seed = append(seed, ensureID(jsonx.Clone(d)))
	}
	r.mu.Lock()
	r.deployments = seed
	r.mu.Unlock()
}

// CoolDown marks a deployment failed.
func (r *Router) CoolDown(modelID string, reason string) {
	r.cooldowns.Add(modelID, reason, r.cooldownTime())
}

// Cooldowns returns currently cooled-down model_ids.
func (r *Router) Cooldowns() []string {
	return r.cooldowns.Active()
}

// ClearCooldown removes a cooldown.
func (r *Router) ClearCooldown(modelID string) {
	r.cooldowns.Clear(modelID)
}

func (r *Router) resolveAlias(modelName string) string {
	if r.cfg == nil {
		return modelName
	}
	aliases := jsonx.AsMap(r.cfg.RouterSetting("model_group_alias"))
	if aliases == nil {
		return modelName
	}
	switch v := aliases[modelName].(type) {
	case string:
		return v
	default:
		if m := jsonx.AsMap(v); m != nil {
			if real := jsonx.Str(m, "model"); real != "" {
				return real
			}
		}
	}
	return modelName
}

func (r *Router) strategy() string {
	if r.cfg == nil {
		return "simple-shuffle"
	}
	if s, ok := r.cfg.RouterSetting("routing_strategy").(string); ok && s != "" {
		return s
	}
	return "simple-shuffle"
}

func (r *Router) cooldownTime() time.Duration {
	if r.cfg == nil {
		return 60 * time.Second
	}
	switch v := r.cfg.RouterSetting("cooldown_time").(type) {
	case int:
		return time.Duration(v) * time.Second
	case int64:
		return time.Duration(v) * time.Second
	case float64:
		return time.Duration(v * float64(time.Second))
	default:
		return 60 * time.Second
	}
}

func ensureID(d map[string]any) map[string]any {
	if info := jsonx.Nested(d, "model_info"); info != nil {
		if id := jsonx.Str(info, "id"); id != "" {
			d["model_id"] = id
			return d
		}
	}
	if id := jsonx.Str(d, "model_id"); id != "" {
		return d
	}
	buf := make([]byte, 16)
	_, _ = rand.Read(buf)
	id := base64.RawURLEncoding.EncodeToString(buf)
	d["model_id"] = id
	info := jsonx.Nested(d, "model_info")
	if info == nil {
		info = map[string]any{}
	}
	info["id"] = id
	d["model_info"] = info
	return d
}

// CooldownCache tracks per-deployment failure cooldowns.
type CooldownCache struct {
	mu   sync.Mutex
	data map[string]cooldown
}

type cooldown struct {
	expires time.Time
	reason  string
}

func NewCooldownCache() *CooldownCache {
	return &CooldownCache{data: map[string]cooldown{}}
}

func (c *CooldownCache) Add(modelID, reason string, d time.Duration) {
	if modelID == "" {
		return
	}
	c.mu.Lock()
	c.data[modelID] = cooldown{expires: time.Now().Add(d), reason: reason}
	c.mu.Unlock()
}

func (c *CooldownCache) CooledDown(modelID string) bool {
	if modelID == "" {
		return false
	}
	c.mu.Lock()
	defer c.mu.Unlock()
	cd, ok := c.data[modelID]
	if !ok {
		return false
	}
	if time.Now().Before(cd.expires) {
		return true
	}
	delete(c.data, modelID)
	return false
}

func (c *CooldownCache) Clear(modelID string) {
	c.mu.Lock()
	delete(c.data, modelID)
	c.mu.Unlock()
}

func (c *CooldownCache) Active() []string {
	c.mu.Lock()
	defer c.mu.Unlock()
	now := time.Now()
	var out []string
	for id, cd := range c.data {
		if now.Before(cd.expires) {
			out = append(out, id)
		}
	}
	return out
}
