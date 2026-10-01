# Retire the legacy real-data endpoint

The `hoymiles-wifi` library exposes two ways to fetch readings, but they return different wire formats: `async_get_real_data_new()` returns `RealDataNewReqDTO`, while the legacy `async_get_real_data()` returns `RealDataReqDTO` — which has no `sgs_data` at all and keys its `pv_data` entries by `pv_sn`/`pv_port` instead of `serial_number`/`port_number`. The old fallback path therefore crashed during metric processing *after* the exporter had already reported the DTU as UP, silently serving stale data under a false-UP state. We poll only `async_get_real_data_new()`; the snapshot module accepts only `RealDataNewReqDTO`.

**Considered options**: normalizing both formats inside the snapshot module. Rejected: it doubles the mapping surface for a path with no evidence it ever fires usefully, and the legacy `PvDataMO` field scalings are unverified.

**Consequences**: a DTU that only serves the legacy endpoint will report `hoymiles_dtu_up 0` — an honest failure — instead of publishing garbage. If field evidence ever shows such firmware, reintroduce support as a second adapter at the reader seam rather than re-adding a silent fallback.
