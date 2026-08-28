# T1 Pipeline Report

Credits: **124** of 360 tranche cap · live calls 124 · cache hits 105

## Gate 2: 33 tickers resolved — PASS - full T2 scope

```json
{
  "s01": {
    "expected_total": 366,
    "fetched": 366,
    "listed": 68,
    "unlisted": 298,
    "listed_symbols": [
      "AADI.JK",
      "ABMM.JK",
      "ADMR.JK",
      "ADRO.JK",
      "AIMS.JK",
      "ALII.JK",
      "AMMN.JK",
      "ANTM.JK",
      "ARCI.JK",
      "ARII.JK",
      "BBRM.JK",
      "BESS.JK",
      "BIPI.JK",
      "BOSS.JK",
      "BRMS.JK",
      "BSML.JK",
      "BSSR.JK",
      "BUMI.JK",
      "BYAN.JK",
      "CANI.JK",
      "CBRE.JK",
      "CNKO.JK",
      "COAL.JK",
      "CUAN.JK",
      "DEWA.JK",
      "DKFT.JK",
      "DOID.JK",
      "DSSA.JK",
      "DWGL.JK",
      "FIRE.JK",
      "GEMS.JK",
      "GTBO.JK",
      "HRUM.JK",
      "IATA.JK",
      "IFSH.JK",
      "INCO.JK",
      "INDY.JK",
      "ITMA.JK",
      "ITMG.JK",
      "KKGI.JK",
      "KOBX.JK",
      "MAHA.JK",
      "MBAP.JK",
      "MBMA.JK",
      "MBSS.JK",
      "MCOL.JK",
      "MDKA.JK",
      "MYOH.JK",
      "NCKL.JK",
      "NICE.JK",
      "NICL.JK",
      "PKPK.JK",
      "PSAB.JK",
      "PSSI.JK",
      "PTBA.JK",
      "PTIS.JK",
      "PTRO.JK",
      "RIGS.JK",
      "RMKE.JK",
      "SGER.JK",
      "SMMT.JK",
      "SMRU.JK",
      "TCPI.JK",
      "TEBE.JK",
      "TOBA.JK",
      "TPMA.JK",
      "TRAM.JK",
      "UNTR.JK"
    ],
    "company_types": {
      "Holding": 47,
      "Contractor": 100,
      "Mine Owner": 188,
      "Trader": 13,
      "Consultant": 2,
      "Manufacturer": 16
    }
  },
  "s02": {
    "by_commodity": {
      "Coal": {
        "expected_total": 946,
        "fetched": 946,
        "with_company_slug": 132,
        "slug_density": 0.14,
        "distinct_slugs": 102,
        "total_area_ha": 4176194.2,
        "page_capped": false
      },
      "Nickel": {
        "expected_total": 401,
        "fetched": 401,
        "with_company_slug": 27,
        "slug_density": 0.067,
        "distinct_slugs": 18,
        "total_area_ha": 1014563.1,
        "page_capped": false
      },
      "Gold": {
        "expected_total": 101,
        "fetched": 101,
        "with_company_slug": 26,
        "slug_density": 0.257,
        "distinct_slugs": 21,
        "total_area_ha": 1215468.5,
        "page_capped": false
      },
      "Copper": {
        "expected_total": 10,
        "fetched": 10,
        "with_company_slug": 9,
        "slug_density": 0.9,
        "distinct_slugs": 8,
        "total_area_ha": 74081.1,
        "page_capped": false
      }
    },
    "unique_licenses": 1454
  },
  "s03": {
    "candidates": 204,
    "selected": 160,
    "dropped": 44,
    "trees_fetched": 160,
    "edges": 193,
    "slugs_with_listed_parent": 128,
    "failures": []
  },
  "gate2": {
    "tickers_resolved": 33,
    "license_holding_slugs": 146,
    "resolved_slugs": 103,
    "unresolved_slugs": 43,
    "unresolved_top_by_area": [
      [
        "pt-berau-coal",
        78004.0
      ],
      [
        "pt-intitirta-primasakti",
        24998.0
      ],
      [
        "pt-asmin-bara-bronang",
        24980.0
      ],
      [
        "pt-suprabari-mapanindo-mineral",
        23940.0
      ],
      [
        "pt-baramutiara-prima",
        19340.0
      ],
      [
        "pt-kartika-selabumi-mining",
        15000.0
      ],
      [
        "pt-gorontalo-sejahtera-mining",
        14570.0
      ],
      [
        "pt-bahari-cakrawala-sebuku",
        14243.0
      ],
      [
        "pt-kalla-arebamma",
        13361.0
      ],
      [
        "pt-celebes-bone-mineral",
        13195.0
      ],
      [
        "pt-bumi-sekundang-enim-energy",
        12880.0
      ],
      [
        "pt-karya-bumi-baratama",
        10211.0
      ],
      [
        "pt-wijaya-eka-sakti",
        10000.0
      ],
      [
        "pt-freeport-indonesia",
        9946.12
      ],
      [
        "pt-jembayan-muarabara",
        6959.0
      ]
    ],
    "resolution_methods": {
      "ownership_tree": 135,
      "api_symbol": 68,
      "name_fuzzy": 1
    },
    "per_ticker": [
      {
        "symbol": "ADMR.JK",
        "slugs": [
          "pt-lahai-coal",
          "pt-sumber-barito-coal",
          "pt-maruwai-coal",
          "pt-juloi-coal",
          "pt-kalteng-coal"
        ],
        "attributable_ha": 146579.0,
        "raw_ha": 146579.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 5
      },
      {
        "symbol": "BRMS.JK",
        "slugs": [
          "pt-citra-palu-mineral",
          "pt-linge-mineral-resources",
          "pt-gorontalo-minerals",
          "pt-suma-heksa-sinergi"
        ],
        "attributable_ha": 130651.344,
        "raw_ha": 153886.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 4
      },
      {
        "symbol": "INCO.JK",
        "slugs": [
          "pt-vale-indonesia"
        ],
        "attributable_ha": 118017.0,
        "raw_ha": 118017.0,
        "methods": [
          "api_symbol"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "ANTM.JK",
        "slugs": [
          "pt-nusa-karya-arindo",
          "pt-aneka-tambang-tbk",
          "pt-sumberdaya-arindo",
          "pt-gag-nikel",
          "pt-nusa-halmahera-minerals",
          "pt-sumbawa-timur-mining"
        ],
        "attributable_ha": 111227.21,
        "raw_ha": 154955.0,
        "methods": [
          "api_symbol",
          "ownership_tree"
        ],
        "license_slug_count": 6
      },
      {
        "symbol": "BYAN.JK",
        "slugs": [
          "pt-gunungbayan-pratamacoal",
          "pt-perkasa-inakakerta",
          "pt-firman-ketaun-perkasa",
          "pt-wahana-baratama-mining",
          "pt-tanur-jaya",
          "pt-tiwa-abadi",
          "pt-brian-anjat-sentosa",
          "pt-fajar-sakti-prima",
          "pt-teguh-sinarabadi",
          "pt-cahaya-alam",
          "pt-dermaga-energi",
          "pt-bara-tabang",
          "pt-bara-sejati",
          "pt-sumber-api",
          "pt-orkida-makmur"
        ],
        "attributable_ha": 93250.634,
        "raw_ha": 95603.56,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 15
      },
      {
        "symbol": "AADI.JK",
        "slugs": [
          "pt-ratah-coal",
          "pt-pari-coal",
          "pt-adaro-indonesia",
          "pt-bukit-enim-energy",
          "pt-laskar-semesta-alam",
          "pt-paramitha-cipta-sarana",
          "pt-semesta-centramas",
          "pt-mustika-indah-permai"
        ],
        "attributable_ha": 90586.90199999999,
        "raw_ha": 106033.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 8
      },
      {
        "symbol": "ITMG.JK",
        "slugs": [
          "pt-indominco-mandiri",
          "pt-trubaindo-coal-mining",
          "pt-bharinto-ekatama",
          "pt-graha-panca-karsa",
          "pt-jorong-barutama-greston",
          "pt-nusa-persada-resources",
          "pt-tepian-indah-sukses"
        ],
        "attributable_ha": 78607.45666400001,
        "raw_ha": 80304.36,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 7
      },
      {
        "symbol": "BUMI.JK",
        "slugs": [
          "pt-kaltim-prima-coal",
          "pt-pendopo-energi-batubara",
          "pt-arutmin-indonesia"
        ],
        "attributable_ha": 77251.598,
        "raw_ha": 113590.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 3
      },
      {
        "symbol": "CUAN.JK",
        "slugs": [
          "pt-multi-tambangjaya-utama",
          "pt-bara-international",
          "pt-daya-bumindo-karunia",
          "pt-tamtama-perkasa",
          "pt-borneo-bangun-banua",
          "pt-intam"
        ],
        "attributable_ha": 68640.14600000001,
        "raw_ha": 86718.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 6
      },
      {
        "symbol": "PTBA.JK",
        "slugs": [
          "pt-bukit-asam-tbk"
        ],
        "attributable_ha": 61512.0,
        "raw_ha": 61512.0,
        "methods": [
          "api_symbol"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "GEMS.JK",
        "slugs": [
          "pt-borneo-indobara",
          "pt-barasentosa-lestari",
          "pt-trisula-kencana-sakti",
          "pt-kuansing-inti-makmur"
        ],
        "attributable_ha": 59054.0,
        "raw_ha": 59054.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 4
      },
      {
        "symbol": "ARCI.JK",
        "slugs": [
          "pt-tambang-tondano-nusajaya",
          "pt-meares-soputan-mining"
        ],
        "attributable_ha": 39817.0,
        "raw_ha": 39817.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "PSAB.JK",
        "slugs": [
          "pt-j-resources-bolaang-mongondow",
          "pt-arafura-surya-alam",
          "pt-sago-prima-pratama"
        ],
        "attributable_ha": 38068.88,
        "raw_ha": 45710.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 3
      },
      {
        "symbol": "HRUM.JK",
        "slugs": [
          "pt-mahakam-sumber-jaya",
          "pt-santan-batubara",
          "pt-bumi-karunia-pertiwi",
          "pt-karya-usaha-pertiwi",
          "pt-arkara-prathama-energi"
        ],
        "attributable_ha": 36571.570199999995,
        "raw_ha": 43197.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 5
      },
      {
        "symbol": "INDY.JK",
        "slugs": [
          "pt-kideco-jaya-agung",
          "pt-masmindo-dwi-area"
        ],
        "attributable_ha": 31672.37,
        "raw_ha": 48277.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "KKGI.JK",
        "slugs": [
          "pt-insani-bara-perkasa",
          "pt-loa-haur"
        ],
        "attributable_ha": 27361.152239999996,
        "raw_ha": 29287.6,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "AMMN.JK",
        "slugs": [
          "pt-amman-mineral-nusa-tenggara"
        ],
        "attributable_ha": 24997.499999999996,
        "raw_ha": 25000.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "BSSR.JK",
        "slugs": [
          "pt-antang-gunung-meratus",
          "pt-baramulti-suksessarana-tbk"
        ],
        "attributable_ha": 24890.5167,
        "raw_ha": 24892.760000000002,
        "methods": [
          "api_symbol",
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "MDKA.JK",
        "slugs": [
          "pt-damai-suksesindo",
          "pt-bumi-suksesindo"
        ],
        "attributable_ha": 11556.46,
        "raw_ha": 11556.46,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "ARII.JK",
        "slugs": [
          "pt-banyan-koalindo-lestari",
          "pt-diva-kencana-borneo",
          "pt-alhasanie"
        ],
        "attributable_ha": 11177.0,
        "raw_ha": 16776.8,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 3
      },
      {
        "symbol": "MBMA.JK",
        "slugs": [
          "pt-sulawesi-cahaya-mineral"
        ],
        "attributable_ha": 10759.9239,
        "raw_ha": 21100.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "MCOL.JK",
        "slugs": [
          "pt-mandiri-intiperkasa"
        ],
        "attributable_ha": 9239.076,
        "raw_ha": 9240.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "NCKL.JK",
        "slugs": [
          "pt-trimegah-bangun-persada-tbk",
          "pt-gane-tambang-sentosa",
          "pt-gane-permai-sentosa"
        ],
        "attributable_ha": 7802.080100000001,
        "raw_ha": 7837.99,
        "methods": [
          "api_symbol",
          "ownership_tree"
        ],
        "license_slug_count": 3
      },
      {
        "symbol": "PKPK.JK",
        "slugs": [
          "pt-tri-oetama-persada"
        ],
        "attributable_ha": 7000.0,
        "raw_ha": 10000.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "DKFT.JK",
        "slugs": [
          "pt-mulia-pacific-resources",
          "pt-itamatra-nusantara",
          "pt-bumi-konawe-abadi"
        ],
        "attributable_ha": 6173.6,
        "raw_ha": 6173.6,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 3
      },
      {
        "symbol": "PTRO.JK",
        "slugs": [
          "pt-christian-eka-pratama"
        ],
        "attributable_ha": 4776.0,
        "raw_ha": 4776.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "SMMT.JK",
        "slugs": [
          "pt-internasional-prima-coal",
          "pt-triaryani"
        ],
        "attributable_ha": 3408.17,
        "raw_ha": 5381.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "MBAP.JK",
        "slugs": [
          "pt-mitrabara-adiperdana-tbk",
          "pt-baradinamika-mudasukses"
        ],
        "attributable_ha": 2766.147,
        "raw_ha": 2766.25,
        "methods": [
          "api_symbol",
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "NICE.JK",
        "slugs": [
          "pt-adhi-kartiko-pratama-tbk"
        ],
        "attributable_ha": 1975.0,
        "raw_ha": 1975.0,
        "methods": [
          "api_symbol"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "TOBA.JK",
        "slugs": [
          "pt-adimitra-baratama-nusantara"
        ],
        "attributable_ha": 1524.9,
        "raw_ha": 2990.0,
        "methods": [
          "ownership_tree"
        ],
        "license_slug_count": 1
      },
      {
        "symbol": "IFSH.JK",
        "slugs": [
          "pt-ifishdeco-tbk",
          "pt-patrindo-jaya-makmur"
        ],
        "attributable_ha": 1250.0,
        "raw_ha": 1300.0,
        "methods": [
          "api_symbol",
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "NICL.JK",
        "slugs": [
          "pt-indrabakti-mustika",
          "pt-pam-mineral-tbk"
        ],
        "attributable_ha": 772.6751999999999,
        "raw_ha": 774.0,
        "methods": [
          "api_symbol",
          "ownership_tree"
        ],
        "license_slug_count": 2
      },
      {
        "symbol": "GTBO.JK",
        "slugs": [
          "pt-garda-tujuh-buana-tbk"
        ],
        "attributable_ha": 710.0,
        "raw_ha": 710.0,
        "methods": [
          "api_symbol"
        ],
        "license_slug_count": 1
      }
    ]
  },
  "gate2_verdict": "PASS - full T2 scope"
}
```
