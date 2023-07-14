# Changelog

<!--next-version-placeholder-->

## v1.18.1 (2023-07-14)

### Fix

* F-string ([`53010b6`](https://github.com/LutherAstrophysics/m23/commit/53010b6270da52584e146f14e41347981d02a8d4))

## v1.18.0 (2023-07-14)

### Feature

* Sanity check no. of images to combine ([`ea1fd11`](https://github.com/LutherAstrophysics/m23/commit/ea1fd111fc838f143e82e0d954f6b3f149be1f22))

## v1.17.0 (2023-07-14)

### Feature

* BREAKING change. require image duration in process configuration ([`7e38441`](https://github.com/LutherAstrophysics/m23/commit/7e384415245d9412ed6dbe41195c076110490583))
* BREAKING change. require image duration in masterflat configuration ([`6cbb47b`](https://github.com/LutherAstrophysics/m23/commit/6cbb47b7633f04510388767f6379bf290b93c48a))

## v1.16.4 (2023-07-12)

### Fix

* Moon distance calculation ([`eb43c98`](https://github.com/LutherAstrophysics/m23/commit/eb43c9865631cd61ea88992a27f9f618e3f7726e))

### Documentation

* Abilty to specify endtime ([`a72fecf`](https://github.com/LutherAstrophysics/m23/commit/a72fecf9ccd69b13c19b05b460a26a02e351ec6d))

## v1.16.3 (2023-07-03)

### Fix

* Normfactors chart ([`b073891`](https://github.com/LutherAstrophysics/m23/commit/b07389168f0eb47b844561151b5a2694d72a0922))

## v1.16.2 (2023-07-03)

### Fix

* Normfactors chart flux log combined folder name ([`4fd0524`](https://github.com/LutherAstrophysics/m23/commit/4fd0524ca8ceba4ead21c342d58c447b5c40f2d3))

## v1.16.1 (2023-07-03)

### Fix

* Flux log combined folder name ([`dfc7f9a`](https://github.com/LutherAstrophysics/m23/commit/dfc7f9a5546559cc9e26252e658a4c37eefe8e8d))

## v1.16.0 (2023-07-03)

### Feature

* Enhace logging ([`5da9571`](https://github.com/LutherAstrophysics/m23/commit/5da9571bbce7ccd194c9a18a6d08e6f12133b13b))

### Fix

* Make cpu_fraction defintion optional ([`0b7a691`](https://github.com/LutherAstrophysics/m23/commit/0b7a6914c2c3d5d9072cc4fe4b46c969563996e9))

## v1.15.0 (2023-07-03)

### Feature

* Save flux log combined from process in a separate folder for EB studies ([`890ccd3`](https://github.com/LutherAstrophysics/m23/commit/890ccd3654219b23423f7a2f33862346b9843034))

## v1.14.0 (2023-07-02)

### Feature

* Use enhanced star bg calculator ([`6aea825`](https://github.com/LutherAstrophysics/m23/commit/6aea825027f18e1f7f7710c123ea90a279985416))

### Documentation

* Add docs ([`1b5ffef`](https://github.com/LutherAstrophysics/m23/commit/1b5ffefaf759f6d1664304656cb0eaacf28be808))

## v1.13.0 (2023-07-02)

### Feature

* Add ability to specify no of processors to use in config file ([`2d5a546`](https://github.com/LutherAstrophysics/m23/commit/2d5a546e05429a7b2f133810ecd6c0401a771918))

## v1.12.0 (2023-07-01)

### Feature

* Add ability to specify endtime to use for night ([`08fabdb`](https://github.com/LutherAstrophysics/m23/commit/08fabdb2cbdcaa7656d5758ca0d824ffc8efd4ae))

## v1.11.5 (2023-06-28)

### Fix

* Handle milliseconds in date-obs in fit header ([`175a26a`](https://github.com/LutherAstrophysics/m23/commit/175a26a812ee0366a70504d39e6c2636f85c726d))

## v1.11.4 (2023-06-28)

### Fix

* Handle milliseconds in date-obs in fit header ([`f304ccc`](https://github.com/LutherAstrophysics/m23/commit/f304cccc76bdf6de98a217864200b4b09b14530c))

## v1.11.3 (2023-06-28)

### Fix

* Remove extra rows/cols from darks,flats during masterflat generation ([`ca88c88`](https://github.com/LutherAstrophysics/m23/commit/ca88c8838da4a3b9fce167b1c6f6289303db88cd))

## v1.11.2 (2023-06-28)

### Fix

* Skip verifying crop region in masterflat generation ([`36de0c4`](https://github.com/LutherAstrophysics/m23/commit/36de0c40d281df6c1985936c08015df954f04960))

### Documentation

* Update rainbow.toml ([`78f1ffd`](https://github.com/LutherAstrophysics/m23/commit/78f1ffd58af2a6bd5327821618b6a6b3067c90d2))

## v1.11.1 (2023-06-28)

### Fix

* Intranight normalization when no of references to normalize to is not 4 ([`7c9f9e0`](https://github.com/LutherAstrophysics/m23/commit/7c9f9e0c9f3031ab79270c6d0b5ecc2428ee2a25))

## v1.11.0 (2023-06-27)

### Feature

* Add support for reading from tab separated logfile combined files ([`12b84e7`](https://github.com/LutherAstrophysics/m23/commit/12b84e78c7e94295b06b90899a553afc5017571c))

### Fix

* Internight bug when some stars didnt have good fluxes after intranight ([`ecdaa8d`](https://github.com/LutherAstrophysics/m23/commit/ecdaa8d7aa1e169218a9c54d4a5e5c0223b68e1c))

## v1.10.1 (2023-06-26)

### Fix

* Intranight normalization elevation method ([`a8e1c75`](https://github.com/LutherAstrophysics/m23/commit/a8e1c75fad9c1cfa44a4f6154aaef4e3e6a9caa8))

## v1.10.0 (2023-06-26)

### Feature

* Perform intranight normalization to same cluster angle ([`d6ce7d0`](https://github.com/LutherAstrophysics/m23/commit/d6ce7d084461df33dd72793368088d7c9c37ab7b))

## v1.9.4 (2023-06-26)

### Fix

* Set appropriate log level ([`8ad5bbd`](https://github.com/LutherAstrophysics/m23/commit/8ad5bbdd0b6488140a44e0e2dcc8b298d8ef5a85))

## v1.9.3 (2023-06-26)

### Performance

* Decrease processor usage ([`33b6443`](https://github.com/LutherAstrophysics/m23/commit/33b6443ab9586475d1f5cc14f5004d213e224c43))

## v1.9.2 (2023-06-26)

### Fix

* Typo ([`909aed0`](https://github.com/LutherAstrophysics/m23/commit/909aed0f459fb0b22050c37a1194db1d59011271))

## v1.9.1 (2023-06-26)

### Fix

* Style ([`360fe7c`](https://github.com/LutherAstrophysics/m23/commit/360fe7cf767222e323a5acfd7582644e11aad1ee))

## v1.9.0 (2023-06-26)

### Feature

* Use extensive logging ([`60afdaf`](https://github.com/LutherAstrophysics/m23/commit/60afdaf00e3bbea2f14265912b0d7d1cf61d3688))

## v1.8.8 (2023-06-26)

### Fix

* Catch any exception encoutered during processing a night, log it and move to next ([`3fca7cb`](https://github.com/LutherAstrophysics/m23/commit/3fca7cbefe3942c17210e0b25d3cca4cebdcf908))

## v1.8.7 (2023-06-26)

### Fix

* Catch exception during internight normalization ([`4988a5c`](https://github.com/LutherAstrophysics/m23/commit/4988a5c082e899eb946e9cbf6e8f693f9ed34771))

## v1.8.6 (2023-06-25)

### Fix

* Use 75% of CPU at max ([`fb8cdc7`](https://github.com/LutherAstrophysics/m23/commit/fb8cdc7e8ca5af9d48498dd8cc3a49002ec84523))

## v1.8.5 (2023-06-25)

### Fix

* Use multiprocessing to use different CPUs to process different nights ([`f761a5b`](https://github.com/LutherAstrophysics/m23/commit/f761a5b797416f45c30b6d3591dd25d2a3c2b2af))

## v1.8.4 (2023-06-25)

### Fix

* Multiprocessing logging in windows ([`4851295`](https://github.com/LutherAstrophysics/m23/commit/4851295a6a5b008779ecc904fc3b33c572124cd7))
* Enhance windows logging support for multiprocessing ([`524cdbb`](https://github.com/LutherAstrophysics/m23/commit/524cdbbf419e1bfa959475999f05e27ede7bb667))

## v1.8.3 (2023-06-25)

### Fix

* Enhance logging ([`7cb23d5`](https://github.com/LutherAstrophysics/m23/commit/7cb23d57e2114794e755dfdcd2de45b6444ed2ff))

## v1.8.2 (2023-06-25)

### Fix

* Use matplotlib in headless mode ([`bbb4bc2`](https://github.com/LutherAstrophysics/m23/commit/bbb4bc26a0be694d848a639fdf7402a3fd3c8e04))

## v1.8.1 (2023-06-25)

### Fix

* Handle case for nan FWHM in extraction ([`954fcb7`](https://github.com/LutherAstrophysics/m23/commit/954fcb7bcbf44cc838de4c45c7fa7942b4cbafba))
* Prevent deleting image data for process safety ([`a200d7f`](https://github.com/LutherAstrophysics/m23/commit/a200d7fdce3dca2c7fd04a489b39911fe95b33bc))

## v1.8.0 (2023-06-25)

### Feature

* Use multiprocessing while running renormalization of multiple nights ([`28acbf6`](https://github.com/LutherAstrophysics/m23/commit/28acbf6cb97b3a84584c51a57853454b940da383))

## v1.7.0 (2023-06-25)

### Feature

* Use multiprocessing to run `ailgn_combine_extract` in parallel ([`9cbc641`](https://github.com/LutherAstrophysics/m23/commit/9cbc64178e2195034f11812ecd255de9c260e720))

### Fix

* Exception in `draw_normfactors_chart` when radii of extraction is different than available radius folders ([`4ce585c`](https://github.com/LutherAstrophysics/m23/commit/4ce585c12ab2f1c667e6b07b4c0480ad92c91737))

## v1.6.1 (2023-06-25)

### Fix

* Include reference fit image as part of the package ([`5d6d766`](https://github.com/LutherAstrophysics/m23/commit/5d6d76600cf08ff22efdd13e9894e7cc453d01e3))

## v1.6.0 (2023-06-25)

### Feature

* Add 2509 and 2510 in ref files ([`30cc695`](https://github.com/LutherAstrophysics/m23/commit/30cc695790326bc47b55980fdc5e2b134cc0065b))

### Documentation

* Mention in readme about reference files section as optional ([`089291d`](https://github.com/LutherAstrophysics/m23/commit/089291d030622cc7a291a773446b1e4b0b901740))

## v1.5.0 (2023-06-25)

### Feature

* Update intranight normalization to normalize to similar elevation images ([`c0dae10`](https://github.com/LutherAstrophysics/m23/commit/c0dae104876d7dcb0ba23be29a2fea9134dee883))
* Make reference files optional ([`84f28d8`](https://github.com/LutherAstrophysics/m23/commit/84f28d8bbc10548400ce570b42c6826342aae94b))

### Fix

* Use natural round in sky bg file ([`bd1f43d`](https://github.com/LutherAstrophysics/m23/commit/bd1f43d94d62c7049f4e67c3e068aaef39520598))

## v1.4.0 (2023-06-24)

### Feature

* Add cols for first/last logfile used in sky bg file ([`7093c10`](https://github.com/LutherAstrophysics/m23/commit/7093c10bbcc3caa679c7c8e2f7e0448691027f5f))
* Account for surrounding boxes in sky adu calc ([`bef88e6`](https://github.com/LutherAstrophysics/m23/commit/bef88e69c78fe56ac16c6ca1f40a59e286171149))

## v1.3.1 (2023-06-24)

### Fix

* Use correct datatype when saving aligned images ([`386cf38`](https://github.com/LutherAstrophysics/m23/commit/386cf3854771c600dd785dfaf5c39962b4ae69c8))
* Use IDL like round during extraction ([`2fc9c35`](https://github.com/LutherAstrophysics/m23/commit/2fc9c3546ad852e6e191a84e7a6589ebe4dc9530))
* Allow sky bg to be 0 ([`6b98aa2`](https://github.com/LutherAstrophysics/m23/commit/6b98aa20acb2ba86831dd5b1f900b3a8f3f632bf))

### Documentation

* Extraction ([`be3e805`](https://github.com/LutherAstrophysics/m23/commit/be3e805b4a515ee2fea0b7561ea09974b4acdf01))

## v1.3.0 (2023-06-22)

### Feature

* Enhance aligned combined file format to matcher alternate harmless patterns ([`38b0375`](https://github.com/LutherAstrophysics/m23/commit/38b03750b3450577cd3cfefe5d653396a544f767))

### Documentation

* Update README.md ([`1766966`](https://github.com/LutherAstrophysics/m23/commit/176696654e1b1cf0c1e4ef717c85f7818eb993a2))

## v1.2.2 (2023-06-22)

### Fix

* Error during sky bg generation ([`2cd4b47`](https://github.com/LutherAstrophysics/m23/commit/2cd4b47f7b4bd4b3f0bc03a6b995920c57be61fa))

### Documentation

* Add photo illustrating commit subjects ([`c2819c6`](https://github.com/LutherAstrophysics/m23/commit/c2819c67846b4e218575b1d8e8c46a5528c7fa56))

## v1.2.1 (2023-06-21)

### Fix

* Masterflat generation bug ([`4c47ca2`](https://github.com/LutherAstrophysics/m23/commit/4c47ca27ae812a95dc164896fd3e67fda0498acd))

## v1.2.0 (2023-06-21)

### Feature

* Add date to the masterflat filename ([`30a86d4`](https://github.com/LutherAstrophysics/m23/commit/30a86d4288fe94dc4dd6d44490d5991326663081))

### Fix

* Add missing f-string ([`0014fe4`](https://github.com/LutherAstrophysics/m23/commit/0014fe4b2dbf713487992b968589472087e1d50d))

## v1.1.0 (2023-06-21)

### Feature

* Write the version number of the m23 in logfile first thing ([`25de6f1`](https://github.com/LutherAstrophysics/m23/commit/25de6f1da66ad56b4d2e5c790b1f54b547dcf4aa))
* Add __version__ variable ([`8b29c9d`](https://github.com/LutherAstrophysics/m23/commit/8b29c9dedcee5fa7138890c9183b2f40a1073739))

### Fix

* Typo in version variable ([`be40d4a`](https://github.com/LutherAstrophysics/m23/commit/be40d4a93c06c75dfc48e4d3d1ed90d95478951b))

### Documentation

* Add release info in contributing section ([`f963e88`](https://github.com/LutherAstrophysics/m23/commit/f963e882e1f09e0867eb64026d5ec9b085a9fb19))
* Mention optional `save_aligned` and `save_combined` options ([`39173cf`](https://github.com/LutherAstrophysics/m23/commit/39173cff6a0a387a7950a524d59940f46e45ccbb))

## v1.0.0 (2023-06-21)



## v0.11.0 (2023-06-21)

### Feature

* Upload release to github releases in addition to other places ([`a8e89b9`](https://github.com/LutherAstrophysics/m23/commit/a8e89b90b011069ce6a851eb52e0a9cf6eb3d00e))

### Fix

* Update fix typo in ci action env var name ([`5e8ef1a`](https://github.com/LutherAstrophysics/m23/commit/5e8ef1a241e091b685d5d379ccecceeb5072d244))
* Update github ci ([`9ba5482`](https://github.com/LutherAstrophysics/m23/commit/9ba54820fd5c60bd61e98bf9c07ff9ff54abcc67))

## v0.10.1 (2023-06-21)

### Fix

* Update build ([`1a7f770`](https://github.com/LutherAstrophysics/m23/commit/1a7f770bb4aa6285c5f3d76546aeebffdf79efd4))

## v0.10.0 (2023-06-21)

### Feature

* Spellfix ([`c4062b8`](https://github.com/LutherAstrophysics/m23/commit/c4062b878d03cc9d69e9a5cf6db1038ba10efce7))

## v0.10.1 (2023-06-21)

### Fix

* Mimic idl in all modules ([`19ca3fd`](https://github.com/LutherAstrophysics/m23/commit/19ca3fdf106af19eb8085a89616ca16e8a22902d))
