# Changelog

## [0.7.0](https://github.com/AdamCaviness/agentic-atlas/compare/v0.6.0...v0.7.0) (2026-07-23)


### Features

* add corpus refresh tooling (corpus-fetch/rescore/refresh) ([1d0cb53](https://github.com/AdamCaviness/agentic-atlas/commit/1d0cb535caa1ad972988bafd89ff9d47ec466870))
* corpus refresh tooling + correct Fresh vs Mature from full clones ([18d46bb](https://github.com/AdamCaviness/agentic-atlas/commit/18d46bbcbab0d3f5742fc3b75229d5bb00fb7525))


### Bug Fixes

* correct Fresh vs Mature scores by re-profiling from full clones ([45f5d75](https://github.com/AdamCaviness/agentic-atlas/commit/45f5d7537627fb3933b71d8a6d91cdc345da8581))

## [0.6.0](https://github.com/AdamCaviness/agentic-atlas/compare/v0.5.0...v0.6.0) (2026-07-23)


### Features

* explorer/report polish, CI gate, and rubric v2 calibration plan + harness ([c0ba96c](https://github.com/AdamCaviness/agentic-atlas/commit/c0ba96c40b949da55166d44d2afee1191f25d0ef))
* **report:** link every profile page home to the Explorer via the brand mark ([94153cd](https://github.com/AdamCaviness/agentic-atlas/commit/94153cdecece82ba67260e658375d930ebd1c9b7))
* **site:** make the explorer card title the profile link; add open-explorer and explain skills ([84ef09c](https://github.com/AdamCaviness/agentic-atlas/commit/84ef09c77043ce1ac9bc6bbc3797a1dee8a3e4f0))

## [0.5.0](https://github.com/AdamCaviness/agentic-atlas/compare/v0.4.0...v0.5.0) (2026-07-23)


### Features

* pre-run profile corpus + interactive discovery site ([b5a2145](https://github.com/AdamCaviness/agentic-atlas/commit/b5a2145bdc5a3c03d5584ea9d933b97ffa7b6b68))
* **site:** pre-run profile corpus + interactive discovery site ([8ec5596](https://github.com/AdamCaviness/agentic-atlas/commit/8ec5596c13257a5036a13587a840c5750df2bd5c))
* **site:** replace 2D scatter with an n-dimensional parallel-coordinates plot ([c0f2b1a](https://github.com/AdamCaviness/agentic-atlas/commit/c0f2b1a45d90d8b1b44ef5074163d568ac649c52))


### Bug Fixes

* **site:** colon not em dash in tooltips/verdicts; external-link icon for new-tab links instead of '(new tab)' text ([46543f3](https://github.com/AdamCaviness/agentic-atlas/commit/46543f357da4a3c07b07afb6e95726d45878f650))
* **ui:** best-matches layout, verdict glyphs, centered vs, active-only center tick; profile page faster crystal + coverage-line signals trigger ([2e49d03](https://github.com/AdamCaviness/agentic-atlas/commit/2e49d036c6ffc7698a6b340513813a68f00eca38))

## [0.4.0](https://github.com/AdamCaviness/agentic-atlas/compare/v0.3.1...v0.4.0) (2026-07-21)


### Features

* **report:** interactive low-poly 3D profile crystal, plus rubric and skill wording ([#14](https://github.com/AdamCaviness/agentic-atlas/issues/14)) ([7aae898](https://github.com/AdamCaviness/agentic-atlas/commit/7aae898a12923d6da7266ce4d522e64b98006e7a))

## [0.3.1](https://github.com/AdamCaviness/agentic-atlas/compare/v0.3.0...v0.3.1) (2026-07-21)


### Bug Fixes

* **report:** refine HTML header wording, layout, and target pill ([#11](https://github.com/AdamCaviness/agentic-atlas/issues/11)) ([e472fe0](https://github.com/AdamCaviness/agentic-atlas/commit/e472fe0b9ea19fce4a4fc0eb44ad8bed7438136b))

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
