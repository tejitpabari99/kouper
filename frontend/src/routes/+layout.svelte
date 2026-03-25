<!--
  Root layout — applied to every route in the app.

  Responsibilities:
    - Imports the global stylesheet (app.css) which defines shared utility
      classes (.screen, .card, .btn-primary, etc.) used throughout all pages.
    - The <slot /> renders the active child route.

  This layout is intentionally minimal. Per-session chrome (breadcrumbs,
  delete button) lives in the nested session layout at
  src/routes/session/[id]/+layout.svelte rather than here.
-->
<script>
  import '../app.css';
</script>

<slot />
