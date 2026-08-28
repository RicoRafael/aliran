# Schema Notes — Round 2 (`etl/spike2.py`)

Credits: **22** · live calls 22 · cache hits 1

```json
[
  {
    "probe": "Q1",
    "question": "Which screener filter form actually returns rows?",
    "ok": true,
    "credits": 4,
    "result": {
      "variants": {
        "oil_gas_coal": {
          "total_count": 89,
          "rows": 30,
          "row_keys": [
            "company_name",
            "symbol"
          ],
          "symbols": [
            "BYAN.JK",
            "DSSA.JK",
            "CUAN.JK",
            "AADI.JK",
            "ADRO.JK",
            "BUMI.JK",
            "ADMR.JK",
            "PTRO.JK",
            "GEMS.JK",
            "PGAS.JK",
            "MEDC.JK",
            "ENRG.JK"
          ],
          "sample": {
            "symbol": "BYAN.JK",
            "company_name": "Bayan Resources Tbk"
          }
        },
        "basic_materials": {
          "total_count": 114,
          "rows": 30,
          "row_keys": [
            "company_name",
            "symbol"
          ],
          "symbols": [
            "AMMN.JK",
            "BRPT.JK",
            "TPIA.JK",
            "EMAS.JK",
            "BRMS.JK",
            "ANTM.JK",
            "MDKA.JK",
            "MBMA.JK",
            "NCKL.JK",
            "INCO.JK",
            "INKP.JK",
            "ARCI.JK"
          ],
          "sample": {
            "symbol": "AMMN.JK",
            "company_name": "PT Amman Mineral Internasional Tbk."
          }
        },
        "symbol_in_plain": {
          "total_count": 0,
          "rows": 0,
          "row_keys": [],
          "symbols": [],
          "sample": null
        },
        "symbol_in_suffixed": {
          "total_count": 2,
          "rows": 2,
          "row_keys": [
            "company_name",
            "symbol"
          ],
          "symbols": [
            "ADRO.JK",
            "PTBA.JK"
          ],
          "sample": {
            "symbol": "ADRO.JK",
            "company_name": "Alamtri Resources Indonesia Tbk"
          }
        }
      },
      "WORKING_FORMS": [
        "oil_gas_coal",
        "basic_materials",
        "symbol_in_suffixed"
      ]
    }
  },
  {
    "probe": "Q2",
    "question": "Do earlier years carry strip_ratio and production_volume?",
    "ok": true,
    "credits": 5,
    "result": {
      "by_year": {
        "Coal_2021": {
          "total_count": 0,
          "rows": 0,
          "with_strip_ratio": 0,
          "with_production": 0,
          "with_company_slug": 0,
          "example_slugs": []
        },
        "Coal_2022": {
          "total_count": 4,
          "rows": 4,
          "with_strip_ratio": 0,
          "with_production": 4,
          "with_company_slug": 4,
          "example_slugs": [
            "lati",
            "binungan",
            "sambarata",
            "gurimbang"
          ]
        },
        "Coal_2023": {
          "total_count": 14,
          "rows": 14,
          "with_strip_ratio": 8,
          "with_production": 12,
          "with_company_slug": 14,
          "example_slugs": [
            "lati",
            "binungan",
            "sambarata",
            "gurimbang"
          ]
        },
        "Nickel_2021": {
          "total_count": 0,
          "rows": 0,
          "with_strip_ratio": 0,
          "with_production": 0,
          "with_company_slug": 0,
          "example_slugs": []
        },
        "Nickel_2022": {
          "total_count": 0,
          "rows": 0,
          "with_strip_ratio": 0,
          "with_production": 0,
          "with_company_slug": 0,
          "example_slugs": []
        },
        "Nickel_2023": {
          "total_count": 0,
          "rows": 0,
          "with_strip_ratio": 0,
          "with_production": 0,
          "with_company_slug": 0,
          "example_slugs": []
        }
      },
      "YEARS_WITH_STRIP_RATIO": [
        "Coal_2023"
      ],
      "YEARS_WITH_PRODUCTION": [
        "Coal_2022",
        "Coal_2023"
      ],
      "A3_VIABLE": false,
      "RLI_VIABLE": true
    }
  },
  {
    "probe": "Q3",
    "question": "Group slug density over 120 filings; is idx_investor_slug a fallback?",
    "ok": true,
    "credits": 4,
    "result": {
      "filings_scanned": 120,
      "with_group_slug": 2,
      "group_density": 0.0167,
      "distinct_groups": [
        "barito-group",
        "garuda-food"
      ],
      "with_investor_slug": 11,
      "investor_density": 0.0917,
      "distinct_investors": [
        "dedie-suherlan",
        "hartarto-ciputra",
        "kiky-suherlan",
        "prajogo-pangestu",
        "sudhamek-agoeng",
        "sugiman-layanto",
        "verah-wahyudi-s-wong"
      ],
      "TRACK_B_VIA_GROUPS": false,
      "TRACK_B_VIA_INVESTORS": false
    }
  },
  {
    "probe": "Q4",
    "question": "How deep is per-company performance/financials/sales data?",
    "ok": true,
    "credits": 9,
    "result": {
      "pt-adaro-indonesia": {
        "performance": {
          "keys": [
            "available_years",
            "data",
            "year"
          ],
          "available_years": [
            2019,
            2020,
            2021,
            2022,
            2023,
            2024
          ],
          "preview": "{\"year\": 2024, \"available_years\": [2019, 2020, 2021, 2022, 2023, 2024], \"data\": [{\"year\": 2024, \"commodity_type\": \"Coal\", \"commodity_sub_type\": \"Thermal Coal\", \"commodity_stats\": {\"unit\": \"Mt\", \"mining_operation_status\": \"production\", \"production_volume\": 48.11, \"sales_volume\": 55.8, \"overburden_removal_volume\": 214.18, \"strip_ratio\": 4.45, \"resources_reserves\": {\"measurement_year\": 2024, \"probable_reserves_Mt\": 245.4, \"proven_reserves_Mt\": 371.5, \"total_reserves_Mt\": 616.9, \"inferred_resources_Mt\": 199.6, \"indicated_resources_Mt\": 597.4, \"measured_resources_Mt\": 2572.8, \"total_resources_Mt\": 3369.8}, \"products\": null}}]}"
        },
        "financials": {
          "error": "HTTPError: 404 Client Error: Not Found for url: https://api.sectors.app/v2/mining/companies/financials/pt-adaro-indonesia/"
        },
        "sales_destination": {
          "error": "HTTPError: 404 Client Error: Not Found for url: https://api.sectors.app/v2/mining/sales-destination/pt-adaro-indonesia/"
        }
      },
      "pt-bukit-asam-tbk": {
        "performance": {
          "keys": [
            "available_years",
            "data",
            "year"
          ],
          "available_years": [
            2019,
            2020,
            2021,
            2022,
            2023,
            2024
          ],
          "preview": "{\"year\": 2024, \"available_years\": [2019, 2020, 2021, 2022, 2023, 2024], \"data\": [{\"year\": 2024, \"commodity_type\": \"Coal\", \"commodity_sub_type\": \"Sub-bituminous\", \"commodity_stats\": {\"unit\": \"Mt\", \"mining_operation_status\": \"production\", \"production_volume\": 43.28, \"sales_volume\": 42.89, \"overburden_removal_volume\": 269.63, \"strip_ratio\": 6.23, \"resources_reserves\": {\"measurement_year\": 2024, \"probable_reserves_Mt\": null, \"proven_reserves_Mt\": null, \"total_reserves_Mt\": 2933.0, \"inferred_resources_Mt\": null, \"indicated_resources_Mt\": null, \"measured_resources_Mt\": null, \"total_resources_Mt\": 5766.0}, \"products\": [{\"product_name\": \"BA-28\", \"calorific_value_kcal\": {\"max\": 2800.0, \"min\": 2800.0}"
        },
        "financials": {
          "error": "HTTPError: 404 Client Error: Not Found for url: https://api.sectors.app/v2/mining/companies/financials/pt-bukit-asam-tbk/"
        },
        "sales_destination": {
          "keys": [
            "data",
            "year"
          ],
          "available_years": null,
          "preview": "{\"year\": 2024, \"data\": {\"Bangladesh\": {\"revenue_usd\": null, \"percentage_of_total_revenue\": null, \"volume\": 42.89, \"percentage_of_sales_volume\": 3.86, \"commodity_type\": \"Coal\", \"unit\": \"Mt\"}, \"Cambodia\": {\"revenue_usd\": null, \"percentage_of_total_revenue\": null, \"volume\": null, \"percentage_of_sales_volume\": 2.26, \"commodity_type\": \"Coal\", \"unit\": \"Mt\"}, \"China\": {\"revenue_usd\": null, \"percentage_of_total_revenue\": null, \"volume\": null, \"percentage_of_sales_volume\": 3.38, \"commodity_type\": \"Coal\", \"unit\": \"Mt\"}, \"Hong Kong\": {\"revenue_usd\": null, \"percentage_of_total_revenue\": null, \"volume\": null, \"percentage_of_sales_volume\": 0.06, \"commodity_type\": \"Coal\", \"unit\": \"Mt\"}, \"India\": {\"revenue_"
        }
      },
      "pt-vale-indonesia": {
        "performance": {
          "keys": [
            "available_years",
            "data",
            "year"
          ],
          "available_years": [
            2024
          ],
          "preview": "{\"year\": 2024, \"available_years\": [2024], \"data\": [{\"year\": 2024, \"commodity_type\": \"Nickel\", \"commodity_sub_type\": \"Limonite & Saprolite Ore\", \"commodity_stats\": {\"unit\": \"wmt\", \"mining_operation_status\": \"production\", \"production_volume\": 14.66, \"sales_volume\": null, \"resources_reserves\": {\"measurement_year\": 2024, \"total_reserves_wmt\": null, \"total_reserves_dmt\": null, \"Ni_reserves_pct\": null, \"Ni_reserves_Kt\": null, \"Co_reserves_pct\": null, \"Co_reserves_Kt\": null, \"Fe_reserves_pct\": null, \"SiO2_reserves_pct\": null, \"MgO_reserves_pct\": null, \"Al2O3_reserves_pct\": null, \"total_resources_wmt\": 482.28, \"total_resources_dmt\": 310.1, \"Ni_resources_pct\": 1.14, \"Ni_resources_Kt\": null, \"Co_resou"
        },
        "financials": {
          "error": "HTTPError: 404 Client Error: Not Found for url: https://api.sectors.app/v2/mining/companies/financials/pt-vale-indonesia/"
        },
        "sales_destination": {
          "error": "HTTPError: 404 Client Error: Not Found for url: https://api.sectors.app/v2/mining/sales-destination/pt-vale-indonesia/"
        }
      }
    }
  }
]
```
