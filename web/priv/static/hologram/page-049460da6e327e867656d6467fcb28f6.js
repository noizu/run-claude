"use strict";(()=>{var r=class{static diff(u){let o=performance.now()-u;return o<1?`${Math.round(o*1e3)} \u03BCs`:`${Math.round(o)} ms`}static start(){return performance.now()}};var p=performance.now();globalThis.Hologram.pageReachableFunctionDefs=m=>{let{Bitstring:u,ERTS:o,HologramBoxedError:g,HologramInterpreterError:b,Interpreter:e,MemoryStorage:x,Type:t,Utils:c}=m;e.defineElixirFunction("Hologram.Router.Helpers","page_bundle_path",1,"public",[{params:s=>[t.variablePattern("page_digest_0")],guards:[],body:s=>t.bitstring([t.bitstringSegment(t.string("/hologram/page-"),{type:"binary"}),t.bitstringSegment(Elixir_String_Chars["to_string/1"](s.vars.page_digest_0),{type:"binary"}),t.bitstringSegment(t.string(".js"),{type:"binary"})])}]),e.defineElixirFunction("Hologram.UI.Runtime","__props__",0,"public",[{params:s=>[],guards:[],body:s=>Elixir_Enum["reverse/1"](t.list([t.tuple([t.atom("page_mounted?"),t.atom("boolean"),t.list([t.tuple([t.atom("from_context"),t.tuple([t.atom("Elixir.Hologram.Runtime"),t.atom("page_mounted?")])])])]),t.tuple([t.atom("page_digest"),t.atom("string"),t.list([t.tuple([t.atom("from_context"),t.tuple([t.atom("Elixir.Hologram.Runtime"),t.atom("page_digest")])])])]),t.tuple([t.atom("instance_id"),t.atom("string"),t.list([t.tuple([t.atom("from_context"),t.tuple([t.atom("Elixir.Hologram.Runtime"),t.atom("instance_id")])])])]),t.tuple([t.atom("initial_page?"),t.atom("boolean"),t.list([t.tuple([t.atom("from_context"),t.tuple([t.atom("Elixir.Hologram.Runtime"),t.atom("initial_page?")])])])]),t.tuple([t.atom("csrf_token"),t.atom("string"),t.list([t.tuple([t.atom("from_context"),t.tuple([t.atom("Elixir.Hologram.Runtime"),t.atom("csrf_token")])])])])]))}]),e.defineElixirFunction("Hologram.UI.Runtime","template",0,"public",[{params:s=>[],guards:[],body:s=>(globalThis.Hologram.return=t.anonymousFunction(1,[{params:n=>[t.variablePattern("vars_0")],guards:[],body:n=>(e.matchOperator(n.vars.vars_0,t.matchPlaceholder(),n),e.updateVarsToMatchedValues(n),t.list([e.case(e.case(e.dotOperator(n.vars.vars_0,t.atom("initial_page?")),[{match:t.variablePattern("x_1"),guards:[i=>Erlang["orelse/2"](l=>Erlang["=:=/2"](l.vars.x_1,t.atom("false")),l=>Erlang["=:=/2"](l.vars.x_1,t.atom("nil")),i)],body:i=>i.vars.x_1},{match:t.matchPlaceholder(),guards:[],body:i=>e.case(e.dotOperator(i.vars.vars_0,t.atom("page_mounted?")),[{match:t.variablePattern("x_2"),guards:[l=>Erlang["orelse/2"](a=>Erlang["=:=/2"](a.vars.x_2,t.atom("false")),a=>Erlang["=:=/2"](a.vars.x_2,t.atom("nil")),l)],body:l=>t.atom("true")},{match:t.matchPlaceholder(),guards:[],body:l=>t.atom("false")}],i)}],n),[{match:t.variablePattern("x_3"),guards:[i=>Erlang["orelse/2"](l=>Erlang["=:=/2"](l.vars.x_3,t.atom("false")),l=>Erlang["=:=/2"](l.vars.x_3,t.atom("nil")),i)],body:i=>t.atom("nil")},{match:t.matchPlaceholder(),guards:[],body:i=>t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("script"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    globalThis.Hologram ??= {};
    globalThis.Hologram._pendingJsInteropActions = [];
    globalThis.Hologram.assetManifest = $ASSET_MANIFEST_JS_PLACEHOLDER;
    globalThis.Hologram.csrfToken = "`)]),t.tuple([t.atom("expression"),t.tuple([e.dotOperator(i.vars.vars_0,t.atom("csrf_token"))])]),t.tuple([t.atom("text"),t.bitstring(`";
    globalThis.Hologram.instanceId = "`)]),t.tuple([t.atom("expression"),t.tuple([e.dotOperator(i.vars.vars_0,t.atom("instance_id"))])]),t.tuple([t.atom("text"),t.bitstring(`";

    globalThis.Hologram.dispatchAction = function(actionName, target, params) {
      globalThis.Hologram._pendingJsInteropActions.push([actionName, target, params]);
    }
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])}],n),t.tuple([t.atom("text"),t.bitstring(`

`)]),e.case(e.case(e.dotOperator(n.vars.vars_0,t.atom("page_mounted?")),[{match:t.variablePattern("x_4"),guards:[i=>Erlang["orelse/2"](l=>Erlang["=:=/2"](l.vars.x_4,t.atom("false")),l=>Erlang["=:=/2"](l.vars.x_4,t.atom("nil")),i)],body:i=>t.atom("true")},{match:t.matchPlaceholder(),guards:[],body:i=>t.atom("false")}],n),[{match:t.atom("false"),guards:[],body:i=>t.atom("nil")},{match:t.atom("true"),guards:[],body:i=>t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("script"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    
      globalThis.Hologram.pageMountData = (deps) => {
        const Type = deps.Type;
        
        return {
          componentRegistry: $COMPONENT_REGISTRY_JS_PLACEHOLDER,
          pageModule: $PAGE_MODULE_JS_PLACEHOLDER,
          pageParams: $PAGE_PARAMS_JS_PLACEHOLDER,
          selfEchoes: $SELF_ECHOES_JS_PLACEHOLDER,
          subReceiptAdds: $SUB_RECEIPT_ADDS_JS_PLACEHOLDER,
          subReceiptDrops: $SUB_RECEIPT_DROPS_JS_PLACEHOLDER
        };
      };
    `)]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])}],n),t.tuple([t.atom("text"),t.bitstring(`

`)]),e.case(e.case(e.dotOperator(n.vars.vars_0,t.atom("initial_page?")),[{match:t.variablePattern("x_5"),guards:[i=>Erlang["orelse/2"](l=>Erlang["=:=/2"](l.vars.x_5,t.atom("false")),l=>Erlang["=:=/2"](l.vars.x_5,t.atom("nil")),i)],body:i=>i.vars.x_5},{match:t.matchPlaceholder(),guards:[],body:i=>e.case(e.dotOperator(i.vars.vars_0,t.atom("page_mounted?")),[{match:t.variablePattern("x_6"),guards:[l=>Erlang["orelse/2"](a=>Erlang["=:=/2"](a.vars.x_6,t.atom("false")),a=>Erlang["=:=/2"](a.vars.x_6,t.atom("nil")),l)],body:l=>t.atom("true")},{match:t.matchPlaceholder(),guards:[],body:l=>t.atom("false")}],i)}],n),[{match:t.variablePattern("x_7"),guards:[i=>Erlang["orelse/2"](l=>Erlang["=:=/2"](l.vars.x_7,t.atom("false")),l=>Erlang["=:=/2"](l.vars.x_7,t.atom("nil")),i)],body:i=>t.atom("nil")},{match:t.matchPlaceholder(),guards:[],body:i=>t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("script"),t.list([t.tuple([t.bitstring("async"),t.list([])]),t.tuple([t.bitstring("src"),t.list([t.tuple([t.atom("expression"),t.tuple([Elixir_Hologram_Router_Helpers["asset_path/1"](t.bitstring("hologram/runtime.js"))])])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])}],n),t.tuple([t.atom("text"),t.bitstring(`

`)]),e.case(e.case(e.dotOperator(n.vars.vars_0,t.atom("page_mounted?")),[{match:t.variablePattern("x_8"),guards:[i=>Erlang["orelse/2"](l=>Erlang["=:=/2"](l.vars.x_8,t.atom("false")),l=>Erlang["=:=/2"](l.vars.x_8,t.atom("nil")),i)],body:i=>t.atom("true")},{match:t.matchPlaceholder(),guards:[],body:i=>t.atom("false")}],n),[{match:t.atom("false"),guards:[],body:i=>t.atom("nil")},{match:t.atom("true"),guards:[],body:i=>t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("script"),t.list([t.tuple([t.bitstring("async"),t.list([])]),t.tuple([t.bitstring("src"),t.list([t.tuple([t.atom("expression"),t.tuple([Elixir_Hologram_Router_Helpers["page_bundle_path/1"](e.dotOperator(i.vars.vars_0,t.atom("page_digest")))])])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])}],n)]))}],s),e.updateVarsToMatchedValues(s),globalThis.Hologram.return)}]),e.defineElixirFunction("RunClaudeWeb.MainLayout","__props__",0,"public",[{params:s=>[],guards:[],body:s=>Elixir_Enum["reverse/1"](t.list([]))}]),e.defineElixirFunction("RunClaudeWeb.MainLayout","template",0,"public",[{params:s=>[],guards:[],body:s=>(globalThis.Hologram.return=t.anonymousFunction(1,[{params:n=>[t.variablePattern("vars_0")],guards:[],body:n=>(e.matchOperator(n.vars.vars_0,t.matchPlaceholder(),n),e.updateVarsToMatchedValues(n),t.list([t.tuple([t.atom("element"),t.bitstring("html"),t.list([t.tuple([t.bitstring("lang"),t.list([t.tuple([t.atom("text"),t.bitstring("en")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("head"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("charset"),t.list([t.tuple([t.atom("text"),t.bitstring("utf-8")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("name"),t.list([t.tuple([t.atom("text"),t.bitstring("viewport")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("width=device-width, initial-scale=1")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("title"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude \u2014 Claude Code. Your models.")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("name"),t.list([t.tuple([t.atom("text"),t.bitstring("description")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude routes Claude Code and OpenCode through a local, self-healing model gateway: map opus/sonnet/haiku/fable tiers to 145+ models across ~26 provider profiles. Your keys, your machine, OAuth passthrough for your Claude subscription.")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("property"),t.list([t.tuple([t.atom("text"),t.bitstring("og:type")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("website")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("property"),t.list([t.tuple([t.atom("text"),t.bitstring("og:title")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude \u2014 Claude Code. Your models.")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("property"),t.list([t.tuple([t.atom("text"),t.bitstring("og:description")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("Keep the Claude Code UX, swap the economics: per-directory model routing through a localhost gateway. 145+ models, ~26 profiles, your keys, no cloud middleman.")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("property"),t.list([t.tuple([t.atom("text"),t.bitstring("og:url")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("https://run-claude.therobotlives.com/")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("meta"),t.list([t.tuple([t.bitstring("name"),t.list([t.tuple([t.atom("text"),t.bitstring("twitter:card")])])]),t.tuple([t.bitstring("content"),t.list([t.tuple([t.atom("text"),t.bitstring("summary")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("link"),t.list([t.tuple([t.bitstring("rel"),t.list([t.tuple([t.atom("text"),t.bitstring("icon")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("/assets/favicon.svg")])])]),t.tuple([t.bitstring("type"),t.list([t.tuple([t.atom("text"),t.bitstring("image/svg+xml")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("link"),t.list([t.tuple([t.bitstring("rel"),t.list([t.tuple([t.atom("text"),t.bitstring("preconnect")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("https://fonts.googleapis.com")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("link"),t.list([t.tuple([t.bitstring("rel"),t.list([t.tuple([t.atom("text"),t.bitstring("preconnect")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("https://fonts.gstatic.com")])])]),t.tuple([t.bitstring("crossorigin"),t.list([t.tuple([t.atom("text"),t.bitstring("anonymous")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("link"),t.list([t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("https://fonts.googleapis.com/css2?family=Inter:wght@400;500;600;700&family=JetBrains+Mono:wght@400;500;700&display=swap")])])]),t.tuple([t.bitstring("rel"),t.list([t.tuple([t.atom("text"),t.bitstring("stylesheet")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("link"),t.list([t.tuple([t.bitstring("rel"),t.list([t.tuple([t.atom("text"),t.bitstring("stylesheet")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("/assets/css/site.css")])])])]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("component"),t.atom("Elixir.Hologram.UI.Runtime"),t.list([]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("body"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("skip-link")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#main")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Skip to content")])])]),t.tuple([t.atom("text"),t.bitstring(`

    `)]),t.tuple([t.atom("element"),t.bitstring("header"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("site-header")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container header-inner")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("brand")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#top")])])]),t.tuple([t.bitstring("aria-label"),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude home")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("span"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("brand-mark")])])]),t.tuple([t.bitstring("aria-hidden"),t.list([t.tuple([t.atom("text"),t.bitstring("true")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("$")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("span"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("brand-name")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("nav"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("site-nav")])])]),t.tuple([t.bitstring("aria-label"),t.list([t.tuple([t.atom("text"),t.bitstring("Primary")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#tiers")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Tiers")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#how")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("How it works")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#faq")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("FAQ")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("btn btn-primary btn-sm")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#install")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Install")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`

    `)]),t.tuple([t.atom("element"),t.bitstring("main"),t.list([t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("main")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("slot"),t.list([]),t.list([])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`

    `)]),t.tuple([t.atom("element"),t.bitstring("footer"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("site-footer")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container footer-inner")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("footer-brand")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude \u2014 a noizu.com project")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("footer-line")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("https://github.com/noizu/run-claude")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("GitHub")])])]),t.tuple([t.atom("text"),t.bitstring(` \xB7
          `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("https://github.com/noizu/run-claude/blob/main/LICENSE")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("MIT licensed")])])]),t.tuple([t.atom("text"),t.bitstring(` \xB7
          This site is Elixir Hologram. \xB7 \xA9 2026
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])])]))}],s),e.updateVarsToMatchedValues(s),globalThis.Hologram.return)}]),e.defineElixirFunction("RunClaudeWeb.Pages.HomePage","__layout_module__",0,"public",[{params:s=>[],guards:[],body:s=>t.atom("Elixir.RunClaudeWeb.MainLayout")}]),e.defineElixirFunction("RunClaudeWeb.Pages.HomePage","__layout_props__",0,"public",[{params:s=>[],guards:[],body:s=>t.list([])}]),e.defineElixirFunction("RunClaudeWeb.Pages.HomePage","__params__",0,"public",[{params:s=>[],guards:[],body:s=>Elixir_Enum["reverse/1"](t.list([]))}]),e.defineElixirFunction("RunClaudeWeb.Pages.HomePage","__route__",0,"public",[{params:s=>[],guards:[],body:s=>t.bitstring("/")}]),e.defineElixirFunction("RunClaudeWeb.Pages.HomePage","template",0,"public",[{params:s=>[],guards:[],body:s=>(globalThis.Hologram.return=t.anonymousFunction(1,[{params:n=>[t.variablePattern("vars_0")],guards:[],body:n=>(e.matchOperator(n.vars.vars_0,t.matchPlaceholder(),n),e.updateVarsToMatchedValues(n),t.list([t.tuple([t.atom("public_comment"),t.list([t.tuple([t.atom("text"),t.bitstring(" HERO ")])])]),t.tuple([t.atom("text"),t.bitstring(`
`)]),t.tuple([t.atom("element"),t.bitstring("section"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("hero")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("top")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container hero-inner")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("eyebrow")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Per-directory model routing \xB7 Claude Code + OpenCode \xB7 MIT")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("h1"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Claude Code. Your models.")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("lede")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      run-claude routes Claude Code \u2014 and OpenCode \u2014 through a local, self-healing model gateway.
      Map the `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("opus")])])]),t.tuple([t.atom("text"),t.bitstring(" / ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("sonnet")])])]),t.tuple([t.atom("text"),t.bitstring(" / ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("haiku")])])]),t.tuple([t.atom("text"),t.bitstring(" / ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("fable")])])]),t.tuple([t.atom("text"),t.bitstring(`
      tiers onto any provider you bring, per project directory. Your keys, your machine,
      your economics.
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("cta-row")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("btn btn-primary btn-lg")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#install")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Install in one command")])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("btn btn-ghost btn-lg")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#tiers")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("See the tier mappings")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("cta-fine")])])])]),t.list([t.tuple([t.atom("element"),t.bitstring("em"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Local-only gateway (127.0.0.1) \xB7 BYO API keys \xB7 MIT licensed")])])])])]),t.tuple([t.atom("text"),t.bitstring(`

    `)]),t.tuple([t.atom("element"),t.bitstring("figure"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("install-block")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("install")])])]),t.tuple([t.bitstring("aria-label"),t.list([t.tuple([t.atom("text"),t.bitstring("Install commands")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("figcaption"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("install-title")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Quick start")])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("pre"),t.list([]),t.list([t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`git clone https://github.com/noizu/run-claude && cd run-claude
make install
run-claude secrets init --generate

cd /path/to/my/project
run-claude set-folder groq && direnv allow
claude`)])])])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])]),t.tuple([t.atom("text"),t.bitstring(`

`)]),t.tuple([t.atom("public_comment"),t.list([t.tuple([t.atom("text"),t.bitstring(" BENEFITS (3-up) ")])])]),t.tuple([t.atom("text"),t.bitstring(`
`)]),t.tuple([t.atom("element"),t.bitstring("section"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("section")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("features")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("h2"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("visually-hidden")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Why run-claude")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("benefit-grid")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("article"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("card")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("h3"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Claude Code, your models")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          Keep the Code UX, swap the economics. Directory-scoped profiles map the
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("opus")])])]),t.tuple([t.atom("text"),t.bitstring(" / ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("sonnet")])])]),t.tuple([t.atom("text"),t.bitstring(" / ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("haiku")])])]),t.tuple([t.atom("text"),t.bitstring(" / ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("fable")])])]),t.tuple([t.atom("text"),t.bitstring(` tiers
          onto 145+ models across ~26 provider profiles. `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("cd")])])]),t.tuple([t.atom("text"),t.bitstring(` into a project and that
          project's models come with it \u2014 no flags, no restarts.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("article"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("card")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("h3"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Your subscription, where it makes sense")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          The `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-plan")])])]),t.tuple([t.atom("text"),t.bitstring(` profile forwards Anthropic requests with your original
          OAuth token \u2014 Pro/Max billing, not API billing \u2014 while other providers in the same
          profile use their own keys. Blend all of it in one profile.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("article"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("card")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("h3"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Local gateway, no middleman")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          Front proxy and gateway run on `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("127.0.0.1")])])]),t.tuple([t.atom("text"),t.bitstring(`; your keys stay in
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("~/.config/run-claude/.secrets")])])]),t.tuple([t.atom("text"),t.bitstring(`. A watchdog daemon restarts crashed proxies
          (~5s poll), a janitor expires idle models after a 15-minute lease, and the default
          gateway is a single static Go binary.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])]),t.tuple([t.atom("text"),t.bitstring(`

`)]),t.tuple([t.atom("public_comment"),t.list([t.tuple([t.atom("text"),t.bitstring(" TIER TABLE ")])])]),t.tuple([t.atom("text"),t.bitstring(`
`)]),t.tuple([t.atom("element"),t.bitstring("section"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("section section-tiers")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("tiers")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("h2"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Tier mappings are one YAML stanza")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("section-lede")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      Every profile maps Claude Code's model tiers. User overrides in
      `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("~/.config/run-claude/profiles/")])])]),t.tuple([t.atom("text"),t.bitstring(" win over built-ins; ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("model: null")])])]),t.tuple([t.atom("text"),t.bitstring(`
      disables an entry.
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("table-scroll")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("table"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("tier-table")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("thead"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("th"),t.list([t.tuple([t.bitstring("scope"),t.list([t.tuple([t.atom("text"),t.bitstring("col")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Profile")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("th"),t.list([t.tuple([t.bitstring("scope"),t.list([t.tuple([t.atom("text"),t.bitstring("col")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("fable")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("th"),t.list([t.tuple([t.bitstring("scope"),t.list([t.tuple([t.atom("text"),t.bitstring("col")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("opus")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("th"),t.list([t.tuple([t.bitstring("scope"),t.list([t.tuple([t.atom("text"),t.bitstring("col")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("sonnet")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("th"),t.list([t.tuple([t.bitstring("scope"),t.list([t.tuple([t.atom("text"),t.bitstring("col")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("haiku")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("tbody"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("anthropic")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("\u2014")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-opus-4")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-sonnet-4")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-3-5-haiku")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-plan ")]),t.tuple([t.atom("element"),t.bitstring("span"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("tag")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("OAuth")])])])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("opus tier")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-opus-4-8")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-sonnet-5")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-haiku-4-5")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("wafer")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("kimi-k3")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.3-flash (max)")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.3-flash (high)")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.3-flash (low)")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("zai-pro")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.3")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.3-flash")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.3-flash")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5-turbo")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("cerebras")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("zai-glm-4.7")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("gemma-4-31b")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("gpt-oss-120b")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("gpt-oss-120b")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("tr"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("alibaba")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("kimi-k3")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("qwen3.8-max")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("glm-5.2")])])]),t.tuple([t.atom("text"),t.bitstring(`
            `)]),t.tuple([t.atom("element"),t.bitstring("td"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("qwen3.6-flash")])])]),t.tuple([t.atom("text"),t.bitstring(`
          `)])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("table-caption")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      Six of ~26 built-in profiles. Groq, DeepSeek, OpenAI, Gemini, Grok, Azure, Mistral,
      Perplexity, OpenRouter, and local Ollama/vLLM ship too \u2014 or write your own.
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])]),t.tuple([t.atom("text"),t.bitstring(`

`)]),t.tuple([t.atom("public_comment"),t.list([t.tuple([t.atom("text"),t.bitstring(" HOW IT WORKS ")])])]),t.tuple([t.atom("text"),t.bitstring(`
`)]),t.tuple([t.atom("element"),t.bitstring("section"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("section")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("how")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("h2"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("How it works")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("ol"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("steps")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("li"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("h3"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Point a directory at a profile")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude set-folder groq && direnv allow")])])]),t.tuple([t.atom("text"),t.bitstring(". One ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(".envrc")])])]),t.tuple([t.atom("text"),t.bitstring(`,
          one stable directory token.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("li"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("h3"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Enter the directory")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          The shell hook hot-registers the profile's models on the running gateway (refcounted,
          leased, janitored) and swaps auth per provider. Anthropic requests keep your OAuth
          token; everything else uses the gateway master key.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("li"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("h3"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Run ")]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude")])])])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          Tier env vars are already set, requests flow through `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("127.0.0.1:4443")])])]),t.tuple([t.atom("text"),t.bitstring(`, and
          the CLI sees the live catalog via its bootstrap endpoint. `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("run-claude with groq")])])]),t.tuple([t.atom("text"),t.bitstring(`
          does the same in a one-shot without pinning the directory.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])]),t.tuple([t.atom("text"),t.bitstring(`

`)]),t.tuple([t.atom("public_comment"),t.list([t.tuple([t.atom("text"),t.bitstring(" FAQ ")])])]),t.tuple([t.atom("text"),t.bitstring(`
`)]),t.tuple([t.atom("element"),t.bitstring("section"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("section section-faq")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("faq")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container container-narrow")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("h2"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Questions you'd ask before trusting it")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-list")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("details"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-item")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("summary"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Do my API keys leave my machine?")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          No. Keys live in `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("~/.config/run-claude/.secrets")])])]),t.tuple([t.atom("text"),t.bitstring(` and are read by the gateway
          on your localhost. Provider calls go from your machine to the provider \u2014 there is no
          hosted relay, no account, and nothing to opt out of.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("details"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-item")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("summary"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Does it break Claude Code features?")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          No. Code still speaks the Anthropic API it already speaks: the front proxy serves the
          CLI's bootstrap endpoint, pre-registers `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("[1m]")])])]),t.tuple([t.atom("text"),t.bitstring(` 1M-context aliases (27 of
          them) so big-context requests route instead of 404, and a provider-compat callback
          strips fields strict providers reject. Tools, MCP, sessions \u2014 unchanged.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("details"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-item")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("summary"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Which providers are supported?")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          Anthropic, OpenAI, Z.AI, Groq, Cerebras, Wafer, Alibaba (Qwen Token Plan), DeepSeek,
          Gemini, Azure, Grok, Mistral, Perplexity, OpenRouter \u2014 plus local Ollama / vLLM /
          LM Studio. ~26 built-in profiles, 145+ model definitions.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("details"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-item")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("summary"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Where does the configuration live?")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          Built-ins ship with the tool. Your overrides in
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("~/.config/run-claude/profiles/")])])]),t.tuple([t.atom("text"),t.bitstring(` and
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("~/.config/run-claude/models.yaml")])])]),t.tuple([t.atom("text"),t.bitstring(` take priority \u2014 same name wins,
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("model: null")])])]),t.tuple([t.atom("text"),t.bitstring(` disables and falls through. Per-directory routing is a
          `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(".envrc")])])]),t.tuple([t.atom("text"),t.bitstring(`.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("details"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-item")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("summary"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Can I still use my Claude Pro/Max subscription?")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`
          Yes \u2014 that's the `)]),t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("claude-plan")])])]),t.tuple([t.atom("text"),t.bitstring(` profile: your original OAuth token is
          forwarded, so subscription billing applies to Claude models while other providers in
          the profile bill their own keys.
        `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("details"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("faq-item")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("summary"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("What's the license?")])])]),t.tuple([t.atom("text"),t.bitstring(`
        `)]),t.tuple([t.atom("element"),t.bitstring("p"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("MIT. Fork it, fork the gateway, ship your own profile pack.")])])]),t.tuple([t.atom("text"),t.bitstring(`
      `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])]),t.tuple([t.atom("text"),t.bitstring(`

`)]),t.tuple([t.atom("public_comment"),t.list([t.tuple([t.atom("text"),t.bitstring(" CLOSING CTA ")])])]),t.tuple([t.atom("text"),t.bitstring(`
`)]),t.tuple([t.atom("element"),t.bitstring("section"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("closing")])])]),t.tuple([t.bitstring("id"),t.list([t.tuple([t.atom("text"),t.bitstring("get-started")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
  `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("container closing-inner")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("h2"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring("Claude Code. Your models.")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("figure"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("install-block")])])]),t.tuple([t.bitstring("aria-label"),t.list([t.tuple([t.atom("text"),t.bitstring("Install commands")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("pre"),t.list([]),t.list([t.tuple([t.atom("element"),t.bitstring("code"),t.list([]),t.list([t.tuple([t.atom("text"),t.bitstring(`git clone https://github.com/noizu/run-claude && cd run-claude
make install
run-claude secrets init --generate`)])])])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)]),t.tuple([t.atom("element"),t.bitstring("div"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("cta-row")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring(`
      `)]),t.tuple([t.atom("element"),t.bitstring("a"),t.list([t.tuple([t.bitstring("class"),t.list([t.tuple([t.atom("text"),t.bitstring("btn btn-primary btn-lg")])])]),t.tuple([t.bitstring("href"),t.list([t.tuple([t.atom("text"),t.bitstring("#install")])])])]),t.list([t.tuple([t.atom("text"),t.bitstring("Install in one command")])])]),t.tuple([t.atom("text"),t.bitstring(`
    `)])])]),t.tuple([t.atom("text"),t.bitstring(`
  `)])])]),t.tuple([t.atom("text"),t.bitstring(`
`)])])])]))}],s),e.updateVarsToMatchedValues(s),globalThis.Hologram.return)}])};globalThis.Hologram.pageScriptLoaded=!0;document.dispatchEvent(new CustomEvent("hologram:pageScriptLoaded"));console.debug("Hologram: page script executed in",r.diff(p));})();
//# sourceMappingURL=page-049460da6e327e867656d6467fcb28f6.js.map
