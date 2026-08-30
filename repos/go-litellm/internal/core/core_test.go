package core

import (
	"reflect"
	"testing"

	"github.com/noizu-labs/go-litellm/internal/router"
)

func TestApplyDeploymentTunablesDropOrder(t *testing.T) {
	lp := map[string]any{
		// Model entry both sets and drops reasoning_effort (the zai sub config
		// shape): the drop applies to the client param, the litellm_params
		// value survives — matching python litellm semantics.
		"reasoning_effort":       "max",
		"additional_drop_params": []any{"reasoning_effort", "thinking"},
		"temperature":            0.7,
	}
	params := map[string]any{
		"model":            "glm-5.3",
		"reasoning_effort": "low",
		"thinking":         map[string]any{"type": "enabled"},
		"max_tokens":       100,
	}
	got := applyDeploymentTunables(params, lp)
	want := map[string]any{
		"model":            "glm-5.3",
		"reasoning_effort": "max",
		"max_tokens":       100,
		"temperature":      0.7,
	}
	if !reflect.DeepEqual(got, want) {
		t.Errorf("got %v, want %v", got, want)
	}
}

func TestPrepareZaiMapping(t *testing.T) {
	rt := router.New(nil)
	rt.Set([]map[string]any{{
		"model_name": "zai-test/glm-5.3",
		"litellm_params": map[string]any{
			"model":                  "anthropic/glm-5.3",
			"api_base":               "https://api.z.ai/api/anthropic",
			"drop_params":            true,
			"additional_drop_params": []any{"context_management", "thinking", "reasoning_effort"},
		},
	}})
	params := map[string]any{
		"model": "zai-test/glm-5.3",
		"messages": []any{
			map[string]any{"role": "user", "content": "hi"},
		},
		"thinking": map[string]any{"type": "enabled", "budget_tokens": 1024},
	}
	p, e := Prepare(rt, nil, params)
	if e != nil {
		t.Fatalf("Prepare: %v", e)
	}
	if got := p.Req.Params["reasoning_effort"]; got != "low" {
		t.Errorf("reasoning_effort = %v, want low", got)
	}
	if _, ok := p.Req.Params["thinking"]; ok {
		t.Error("thinking should have been dropped on a zai route")
	}
}
