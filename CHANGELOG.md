# Changelog

## [0.3.0](https://github.com/AdamCaviness/agentic-atlas/compare/v0.2.0...v0.3.0) (2026-07-20)


### Features

* **plugin:** ship agentic-atlas as a plugin hosting the run skill ([#8](https://github.com/AdamCaviness/agentic-atlas/issues/8)) ([7eda1d5](https://github.com/AdamCaviness/agentic-atlas/commit/7eda1d51f8d5afa14d358c283f64c0d444241838))

## [0.2.0](https://github.com/AdamCaviness/agentic-atlas/compare/v0.1.0...v0.2.0) (2026-07-20)


### Features

* add html report format ([dd6300c](https://github.com/AdamCaviness/agentic-atlas/commit/dd6300c6addde0cd294b79b4c9d4394ba4e886de))
* add path_count measured signal ([be90c28](https://github.com/AdamCaviness/agentic-atlas/commit/be90c283515d874de604ea9c4943355882c390b1))
* curate v1 rubric to 12 axes; fix recursive glob matching ([9b5316b](https://github.com/AdamCaviness/agentic-atlas/commit/9b5316b48c0669633f63938fa01926b23c806281))
* html report format + honest handling of unreadable targets ([dcc8492](https://github.com/AdamCaviness/agentic-atlas/commit/dcc84922ed04dd277c9f48c0d88878f5a0fe83c1))
* path_count signal + make pc3/solo-team discriminate (rubric v1.4.0) ([cc4f89c](https://github.com/AdamCaviness/agentic-atlas/commit/cc4f89c702485d70988a6e6c2a5361c3bd2f94cb))
* **rubric:** add plain-language pole meanings shown per axis in the report ([d84ee36](https://github.com/AdamCaviness/agentic-atlas/commit/d84ee36f1ba49296123d447c3a8005ea453f5a47))
* **rubric:** plain-language pole meanings shown per axis in the report ([33dd3a0](https://github.com/AdamCaviness/agentic-atlas/commit/33dd3a056575e0e4adc748ad9cdac3ae3f9b65eb))
* wire AnthropicJudge into the CLI (--judge anthropic) ([59c3114](https://github.com/AdamCaviness/agentic-atlas/commit/59c3114dfc9b9844d554d864da73210dc97a94fc))


### Bug Fixes

* exclude vendored third-party dirs from the corpus ([8a803f7](https://github.com/AdamCaviness/agentic-atlas/commit/8a803f786424426c7423b928e7bd54ffde67ff31))
* exclude vendored third-party dirs from the corpus ([563bee5](https://github.com/AdamCaviness/agentic-atlas/commit/563bee563b0b9ce1a4da92c39b1fa1026b4e2cdb))
* leave measured signals unresolved on unreadable targets ([070bd7d](https://github.com/AdamCaviness/agentic-atlas/commit/070bd7d753f04d5255a2c74b2860ce85285e6dd1))
* **report:** render an exactly-neutral score as neutral, not +0.0 ([0462431](https://github.com/AdamCaviness/agentic-atlas/commit/0462431b4f446286db90161eb7cff0096678c3a2))
* **rubric:** make pc3 and solo-team discriminate via path_count ([d65856d](https://github.com/AdamCaviness/agentic-atlas/commit/d65856d24a69bc96091ebfc668ea9b12ff78564c))
* **rubric:** recalibrate indicator values to remove pole saturation ([dfe0cb9](https://github.com/AdamCaviness/agentic-atlas/commit/dfe0cb90505c22fce798be2f270c30c2d247286e))
* **rubric:** recalibrate to remove pole saturation + neutral-score rendering ([27f836f](https://github.com/AdamCaviness/agentic-atlas/commit/27f836f802b6d8760492ff5ccf520c80e362327f))


### Refactoring

* per-axis rubric directories with generated README scoring blocks ([89d2273](https://github.com/AdamCaviness/agentic-atlas/commit/89d2273e209cd3d090d4a3059146a93b3bd944a2))
