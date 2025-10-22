# HOW_TO_WIRE_PERSONAS.md
1) Place these files:
   - ./personas/lenses.yaml
   - ./router/persona_router.yaml
   - ./overlays/lens_overlays.yaml

2) Reference in your runtime/engine:
   imports:
     persona_lenses: ./personas/lenses.yaml
     persona_router: ./router/persona_router.yaml
     lens_overlays: ./overlays/lens_overlays.yaml

3) Extend inference_profile.yaml:
   profile:
     persona:
       enabled: true
       router_file: ./router/persona_router.yaml
       lenses_file: ./personas/lenses.yaml
       overlays_file: ./overlays/lens_overlays.yaml

4) At intake (segmentation step), allow optional user field:
   input.meta.persona: ["P_EXEC","P_ANALYST"]

5) During reasoning:
   - After segments & mirror scan, resolve active personas via router + user input.
   - Apply lens_overlays:
       * Adjust gate weights (delta then renormalize; obey hard_caps).
       * Merge tone_mods into N9 (Style) outputs.
       * Prefer persona section_order unless schema forbids.
   - Continue with Metatron → SC@k → Reflexion → Crown Verify.

6) Non‑negotiables (safety/quality):
   - Persona NEVER overrides facts, schema, constraints, or mirror caps.
   - If Crown Verify fails, drop persona effects and retry once.
