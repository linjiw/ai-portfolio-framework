window.AI_FRAMEWORK_DATA = {
  asOf: "2026-05-23",
  dataDate: "2026-05-21",
  reviewDate: "2026-05-23",
  title: "Trusted Execution of Intelligence",
  subtitle:
    "A control-rights portfolio and review system for agentic AI infrastructure.",
  summary:
    "The framework treats intelligence as becoming abundant and trusted execution as the scarce economic layer. Positions express control over capacity, cost, authority, outcome verification, physical AI optionality, and dry powder.",
  decisionProcess: {
    thesis:
      "The portfolio is a public paper test of one question: if intelligence keeps getting cheaper, which public companies control the trusted execution layer around it?",
    choiceRationale: [
      {
        label: "Core compounders",
        weight: "57%",
        text:
          "Microsoft, Google, and Broadcom receive the largest allocation because they can combine model capacity, enterprise authority, workflow distribution, and custom AI infrastructure."
      },
      {
        label: "Bottleneck cyclicals",
        weight: "18%",
        text:
          "SK hynix, NVIDIA, and TSMC express physical constraints in HBM, accelerators, foundry, packaging, and AI factory architecture. They are sized below the core because the cycle risk is higher."
      },
      {
        label: "Vertical verifiers",
        weight: "8%",
        text:
          "MSCI, Moody's, S&P Global, and Veeva are small positions because they test whether trusted data, ratings, regulated workflow, and domain verification become outcome-control assets."
      },
      {
        label: "Optionality and infrastructure",
        weight: "17%",
        text:
          "Teradyne covers semiconductor test and physical-AI optionality, while Constellation, Vertiv, and cash cover power, thermal, and regime-change risk."
      }
    ],
    rules: [
      "Start from control rights, not ticker popularity: capacity, cost, authority, outcome verification, physical AI, and dry powder.",
      "Require every holding to have a thesis, evidence, risks, a watch item, and a falsifier before it earns a target weight.",
      "Size positions by framework role, conviction, cyclicality, evidence quality, and downside path; cash is an explicit risk-control asset.",
      "Use signals to create review work, not automatic trades. Capability, cost, and trust plateau alerts must be reviewed before any rebalance.",
      "Update market prices daily, review indicators monthly, refresh control-right scores quarterly, and keep the paper portfolio auditable."
    ],
    gates: [
      {
        label: "Capability gate",
        text:
          "If long-horizon agent progress stalls, the portfolio shifts from expansion assumptions to framework review."
      },
      {
        label: "Economics gate",
        text:
          "If verified-task cost stops improving after accounting for quality, latency, and human review minutes, cost-control exposure needs reassessment."
      },
      {
        label: "Trust gate",
        text:
          "If enterprise agents do not gain governed write and execute permission, authority and outcome-control positions lose part of their premise."
      },
      {
        label: "Valuation gate",
        text:
          "If the thesis is intact but valuations reset, cash can be deployed manually into the strongest control-right gaps."
      }
    ]
  },
  allocation: [
    { label: "Core compounders", value: 57 },
    { label: "Bottleneck cyclicals", value: 18 },
    { label: "Vertical verifier basket", value: 8 },
    { label: "Asymmetric optionality", value: 7 },
    { label: "Cash", value: 10 }
  ],
  exposures: [
    {
      layer: "Capacity",
      value: 42,
      holdings: "SK Hynix, NVDA, TSM, AVGO, CEG, TER, VRT"
    },
    { layer: "Authority", value: 33, holdings: "MSFT, GOOGL" },
    { layer: "Outcome", value: 26, holdings: "MSFT, GOOGL, MSCI, MCO, SPGI, VEEV" },
    { layer: "Cost", value: 18, holdings: "GOOGL, AVGO, NVDA" },
    { layer: "Risk control", value: 10, holdings: "Cash" },
    { layer: "Physical AI", value: 2, holdings: "TER" }
  ],
  monitoringQuestions: [
    {
      label: "Capability",
      question: "Does agent task horizon keep extending?",
      status: "Watch",
      observed_value: "METR-style time horizon remains the main public proxy; exact cadence is manually reviewed.",
      current_value: "manual review",
      unit: "qualitative",
      threshold: "doubling time >180 days",
      direction: "above_threshold_bad",
      status_rule: "Watch until the public task-horizon trend shows sustained slowing.",
      source_claim_id: "framework-capability-horizon",
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      trigger: "If METR doubling time moves above 180 days, run framework review.",
      sources: ["metr-home", "metr-long-tasks"]
    },
    {
      label: "Economics",
      question: "Does risk-adjusted cost per verified task keep falling?",
      status: "Data gap",
      observed_value: "No complete public TCAO series; token prices and benchmark quality are partial inputs.",
      current_value: "not directly observed",
      unit: "proxy basket",
      threshold: "TCAO fails to improve for 2 quarters",
      direction: "no_improvement_bad",
      status_rule: "Data gap until token, benchmark, latency, and review-minute proxies are combined.",
      source_claim_id: "framework-cost-proxy",
      confidence: "Low",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      trigger:
        "No public series directly measures TCAO; build it from model prices, benchmark quality, latency, and human review minutes.",
      sources: ["epoch-inference-prices", "openai-swebench"]
    },
    {
      label: "Trust",
      question: "Do enterprise agents gain write and execute permission?",
      status: "High review",
      observed_value: "Product surfaces exist, but broad production write-permission penetration remains unproven.",
      current_value: "unproven",
      unit: "enterprise penetration",
      threshold: "<10% Fortune 500 write-permission penetration by Q2 2027",
      direction: "below_threshold_bad",
      status_rule: "High review until production write/execute permissions are disclosed or surveyed.",
      source_claim_id: "framework-trust-permission",
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      trigger:
        "If Fortune 500 write-permission penetration stalls below 10%, reassess authority.",
      sources: ["msft-agent365", "mcp-tools-arxiv"]
    }
  ],
  signals: [
    {
      type: "Plateau detection",
      severity: "Medium",
      target: "Capability",
      action: "Monitor monthly",
      observed_value: "Task-horizon trend is supportive, but needs manual paper/model-release updates.",
      current_value: "manual review",
      unit: "qualitative",
      threshold: "doubling time >180 days",
      direction: "above_threshold_bad",
      status_rule: "Escalate if capability horizon stalls beyond threshold.",
      source_claim_id: "framework-capability-horizon",
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      text:
        "METR's task-horizon framework is thesis-supportive, but the qualitative frontier indicator still needs manual updates after papers and conferences.",
      sources: ["metr-home", "metr-long-tasks"]
    },
    {
      type: "Plateau detection",
      severity: "Info",
      target: "Cost",
      action: "Collect data",
      observed_value: "Inference price trend is measurable; verified-task total cost remains incomplete.",
      current_value: "partial proxy",
      unit: "proxy basket",
      threshold: "verified-task total cost not improving",
      direction: "no_improvement_bad",
      status_rule: "Keep as data gap until TCAO proxy is populated.",
      source_claim_id: "framework-cost-proxy",
      confidence: "Low",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      text:
        "Risk-adjusted cost per verified task is still a data gap; token price and benchmark score are inputs, not the complete enterprise cost.",
      sources: ["epoch-inference-prices", "openai-swebench"]
    },
    {
      type: "Plateau detection",
      severity: "High",
      target: "Authority",
      action: "Framework review",
      observed_value: "Authority products are emerging; production write/execute adoption is the binding unknown.",
      current_value: "unproven",
      unit: "enterprise penetration",
      threshold: "<10% Fortune 500 write-permission penetration by Q2 2027",
      direction: "below_threshold_bad",
      status_rule: "Escalate if authority products fail to convert into production permissions.",
      source_claim_id: "framework-trust-permission",
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      text:
        "Human expert review minutes remain a binding bottleneck until production permissioning, routing, and audit evidence improves.",
      sources: ["msft-agent365", "mcp-tools-arxiv"]
    },
    {
      type: "Watchlist gap",
      severity: "Info",
      target: "Agent runtime",
      action: "No forced public proxy",
      observed_value: "Public-market exposure remains indirect through identity, observability, and data platforms.",
      current_value: "no pure public proxy",
      unit: "coverage",
      threshold: "agent infra revenue >10% of vendor revenue",
      direction: "watchlist_trigger",
      status_rule: "Revisit portfolio mapping when a public vendor discloses material agent-runtime revenue.",
      source_claim_id: "framework-agent-runtime-gap",
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-06-22",
      text:
        "Track agent security, MCP gateway, credential vault, policy-as-code, and observability names; public-market proxies are still imperfect.",
      sources: ["mcp-tools-arxiv", "kensho-mcp"]
    }
  ],
  watchlist: {
    stage: "Memory watchlist",
    objective:
      "Compare MU and SK Hynix as HBM and memory re-rating candidates without changing current holdings.",
    policy:
      "Watchlist entries create evidence, valuation, filing, and bear-case review work only. They cannot add a position, alter target weights, or change conviction without a later human decision log.",
    boundary: "human review only",
    items: [
      {
        ticker: "MU",
        name: "Micron Technology",
        status: "watchlist_not_position",
        statusLabel: "watchlist only",
        role: "HBM re-rating candidate",
        priority: "high",
        nextReviewDue: "2026-06-24",
        decisionBoundary: "No position change from watchlist data",
        coreQuestion:
          "Is Micron becoming a contracted AI-memory supplier, or is the market simply annualizing a peak memory cycle?",
        thesisToTest:
          "Micron has the cleanest potential re-rating setup if HBM4, HBM4E customization, SCAs, and data-center NAND shift the business from spot-cycle memory toward durable strategic supply. The watchlist burden is to prove durability before treating MU like a framework holding.",
        keySignals: [
          {
            label: "Q3 guide",
            value: "GM ~81%",
            interpretation:
              "Official FQ2 2026 materials guide to about 81% gross margin; the next earnings print is the first durability test."
          },
          {
            label: "HBM4 ramp",
            value: "Volume shipments",
            interpretation:
              "Micron says HBM4 36GB 12H volume shipments began in calendar Q1 2026 and are designed for NVIDIA Vera Rubin."
          },
          {
            label: "SCA evidence",
            value: "First 5-year SCA",
            interpretation:
              "Strategic customer agreements are the key test for whether memory demand is becoming contracted instead of purely cyclical."
          },
          {
            label: "Portfolio status",
            value: "0% target weight",
            interpretation:
              "MU remains outside the portfolio until source-linked evidence, valuation, and falsifier thresholds are reviewed."
          }
        ],
        watchMetrics: [
          {
            metric_id: "mu_gross_margin_durability",
            label: "Gross margin durability",
            state: "watching",
            cadence: "quarterly",
            trigger:
              "FQ3 actual gross margin near or above guide supports pricing power; a break below 80% requires bear-case review."
          },
          {
            metric_id: "mu_hbm4_hbm4e_ramp",
            label: "HBM4 / HBM4E ramp evidence",
            state: "watching",
            cadence: "quarterly",
            trigger:
              "Track HBM4 yield/ramp language, HBM4 16-high sampling, and HBM4E 1-gamma roadmap disclosure."
          },
          {
            metric_id: "mu_sca_count_quality",
            label: "SCA count and quality",
            state: "unknown",
            cadence: "quarterly",
            trigger:
              "Watch for additional multi-year SCAs and any take-or-pay or volume-commitment language."
          },
          {
            metric_id: "mu_supply_capex_discipline",
            label: "Supply discipline versus greenfield capex",
            state: "watching",
            cadence: "quarterly",
            trigger:
              "Review whether Idaho, New York, Tongluo, Singapore, and Hiroshima spend improves strategic supply or creates 2028 oversupply risk."
          }
        ],
        evidenceNeeded: [
          "Official disclosure of HBM revenue mix or enough segment detail to infer HBM contribution without relying on market-share guesses.",
          "Evidence that SCAs are durable commitments rather than looser long-term agreements with limited pricing protection.",
          "Customer or platform evidence that HBM4E customization materially raises switching cost.",
          "A valuation snapshot with method and source before any position-sizing discussion."
        ],
        bearCase: [
          "Samsung or SK Hynix qualification progress normalizes HBM scarcity faster than expected.",
          "The apparent demand shortage is partly double ordering or strategic stockpiling.",
          "Large greenfield capex builds future oversupply before SCAs prove durable.",
          "China exposure or export-control risk creates a non-operating drawdown."
        ],
        falsifier:
          "Micron misses the FQ3 gross-margin guide materially, fails to add credible SCA evidence, or HBM4/HBM4E commentary weakens while capex intensity accelerates.",
        nextAction: {
          type: "earnings_checklist",
          priority: "high",
          question:
            "Build a Q3 FY2026 review checklist for gross margin, HBM ramp, SCA additions, capex discipline, and data-center NAND.",
          successCondition:
            "Primary-source earnings materials can map each watch metric to confirming, watching, deteriorating, or unknown."
        },
        decisionProcess: [
          {
            step: "Evidence first",
            text:
              "Treat the JPM conference notes as useful prompts, but promote only official filings, company materials, or clearly attributed transcripts into evidence."
          },
          {
            step: "Compare against SK Hynix",
            text:
              "MU must show better re-rating asymmetry than the existing SK Hynix HBM exposure after valuation and cycle risk."
          },
          {
            step: "No automatic add",
            text:
              "A watchlist score can only create review work; a future weight change would need a decision-log entry and updated framework rationale."
          }
        ],
        source_ids: [
          "micron-q2-2026-results",
          "micron-q2-2026-deck",
          "micron-jpm-2026",
          "micron-sec-submissions",
          "asml-2025-results"
        ]
      },
      {
        ticker: "000660.KS",
        name: "SK Hynix",
        status: "portfolio_holding_watch",
        statusLabel: "holding watch",
        role: "Existing HBM bottleneck holding",
        priority: "high",
        nextReviewDue: "2026-08-22",
        decisionBoundary: "No target-weight change; review state only",
        coreQuestion:
          "Does SK Hynix retain HBM leadership as HBM4, High-NA EUV, and Samsung/Micron qualification pressure evolve?",
        thesisToTest:
          "SK Hynix remains the portfolio's most direct HBM bottleneck exposure. The watchlist exists because the position is already owned, but the evidence state must track whether the leadership premium is widening or being competed away.",
        keySignals: [
          {
            label: "FY2025 record",
            value: "AI memory driver",
            interpretation:
              "Official FY2025 results cite high-value products including HBM as a driver of record annual and quarterly performance."
          },
          {
            label: "Q1 2026",
            value: "72% operating margin",
            interpretation:
              "Official Q1 2026 results show extraordinary profitability; the review question is how durable this is through HBM4 supply competition."
          },
          {
            label: "HBM4",
            value: "Mass-production ready",
            interpretation:
              "SK Hynix says HBM4 development and mass-production preparation were completed first in the industry."
          },
          {
            label: "High-NA EUV",
            value: "M16 system assembled",
            interpretation:
              "The company says it assembled ASML's EXE:5200B High-NA EUV system for next-generation memory production."
          }
        ],
        watchMetrics: [
          {
            metric_id: "skhynix_hbm_revenue_commentary",
            label: "HBM revenue and mix commentary",
            state: "watching",
            cadence: "quarterly",
            trigger:
              "Track whether HBM remains the high-value product driver or whether conventional DRAM is doing more of the work."
          },
          {
            metric_id: "skhynix_hbm4_customer_qualification",
            label: "HBM4 customer qualification",
            state: "improving",
            cadence: "quarterly",
            trigger:
              "Look for customer-request language, shipment timing, and signs that NVIDIA/Samsung/Micron share is shifting."
          },
          {
            metric_id: "skhynix_euv_high_na_transition",
            label: "EUV / High-NA transition",
            state: "watching",
            cadence: "semiannual",
            trigger:
              "Track whether EUV adoption improves 1c/next-node cost and density rather than only signaling capex escalation."
          },
          {
            metric_id: "skhynix_memory_cycle_risk",
            label: "Memory-cycle risk",
            state: "watching",
            cadence: "quarterly",
            trigger:
              "Review DRAM/NAND pricing, capex plans, KRW exposure, and customer concentration."
          }
        ],
        evidenceNeeded: [
          "Primary-source HBM4 shipment and qualification updates by customer or platform where available.",
          "Disclosure that separates HBM-led margin durability from broad DRAM price-cycle strength.",
          "Evidence that High-NA and EUV capex improves cost competitiveness rather than just increasing fixed-cost risk.",
          "Explicit bear-case tracking for Samsung and Micron gaining Rubin-generation share."
        ],
        bearCase: [
          "Samsung regains meaningful NVIDIA HBM4/HBM4E share and compresses SK Hynix pricing power.",
          "Micron's SCA and HBM4E customization narrative closes the quality gap faster than expected.",
          "A hyperscaler capex slowdown hits HBM, server DRAM, eSSD, and portfolio capex exposure at the same time.",
          "KRW, Korea geopolitical risk, or export controls dominate stock performance despite good operating data."
        ],
        falsifier:
          "Samsung or Micron captures material Rubin-generation HBM share, SK Hynix margin language deteriorates, or HBM leadership stops translating into financial outperformance.",
        nextAction: {
          type: "holding_review",
          priority: "high",
          question:
            "Compare SK Hynix Q2/Q3 evidence against MU's next earnings evidence before changing any memory exposure language.",
          successCondition:
            "The review can explain whether SK Hynix still has the best risk-adjusted HBM exposure in the framework."
        },
        decisionProcess: [
          {
            step: "Separate holding from thesis",
            text:
              "Owning SK Hynix does not mean HBM leadership is assumed; each quarter must update the evidence state."
          },
          {
            step: "Track competitor displacement",
            text:
              "The key bear case is not weak demand alone, but Samsung or Micron taking share while supply expands."
          },
          {
            step: "Preserve boundary",
            text:
              "Watchlist deterioration triggers review, not an automatic trim; any change requires a decision-log entry."
          }
        ],
        source_ids: [
          "skhynix-hbm4",
          "skhynix-q1-2026",
          "skhynix-fy2025-results",
          "skhynix-high-na-euv",
          "asml-2025-results"
        ]
      }
    ],
    comparison: [
      {
        dimension: "Framework role",
        micron:
          "Candidate for a new memory re-rating sleeve if SCAs and HBM4E customization make earnings less cyclical.",
        skHynix:
          "Existing bottleneck-cyclical holding that already expresses HBM leadership inside the portfolio.",
        decisionUse:
          "MU must improve portfolio evidence quality or asymmetry beyond what SK Hynix already provides."
      },
      {
        dimension: "Evidence quality",
        micron:
          "Strong official Q2 materials, but HBM revenue mix and SCA economics still need sharper disclosure.",
        skHynix:
          "Official releases support HBM4 readiness, record results, and High-NA EUV adoption, but customer-share detail remains limited.",
        decisionUse:
          "Prefer primary-source evidence over conference-note summaries before updating thesis status."
      },
      {
        dimension: "Main falsifier",
        micron:
          "Cycle peak: margin guide fails, SCAs do not multiply, or capex expands faster than durable contracted demand.",
        skHynix:
          "Leadership erosion: Samsung or Micron wins material HBM4/HBM4E share and margin durability weakens.",
        decisionUse:
          "The two names should be reviewed as substitutes before adding any memory beta."
      },
      {
        dimension: "Valuation discipline",
        micron:
          "Requires a sourced valuation snapshot before any framework weight discussion because sentiment has moved quickly.",
        skHynix:
          "Already sized as a cyclical bottleneck holding; valuation changes should affect review language before weight.",
        decisionUse:
          "Do not let HBM excitement bypass the valuation gate."
      }
    ]
  },
  claims: [
    {
      claim_id: "framework-capability-horizon",
      source_id: "metr-long-tasks",
      entity: "Capability",
      claim: "Long-horizon task completion is the cleanest public proxy for frontier agent capability.",
      evidence_type: "research_paper",
      metric: "task horizon",
      quote_or_excerpt: "Task-horizon benchmark methodology",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "framework-cost-proxy",
      source_id: "epoch-inference-prices",
      entity: "Cost",
      claim: "Inference price trends are useful but incomplete proxies for verified-task economics.",
      evidence_type: "research_dataset",
      metric: "LLM inference price trend",
      quote_or_excerpt: "Public inference-price series",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "framework-trust-permission",
      source_id: "msft-agent365",
      entity: "Authority",
      claim: "Enterprise trust depends on whether governed agents gain production write and execute permissions.",
      evidence_type: "company_product_page",
      metric: "agent governance and permissioning product surface",
      quote_or_excerpt: "Agent management and governance positioning",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "framework-agent-runtime-gap",
      source_id: "mcp-tools-arxiv",
      entity: "Agent runtime",
      claim: "Agent-to-tool usage creates an infrastructure layer, but public-market exposure remains indirect.",
      evidence_type: "research_paper",
      metric: "MCP/tool-use ecosystem evidence",
      quote_or_excerpt: "Agent tool-use protocol research",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "msft-agent-authority",
      source_id: "msft-agent365",
      entity: "MSFT",
      claim: "Agent 365 gives Microsoft a product surface for enterprise agent governance.",
      evidence_type: "company_product_page",
      metric: "agent control-plane positioning",
      quote_or_excerpt: "Agent management and governance product surface",
      retrieved_at: "2026-05-22",
      confidence: "High"
    },
    {
      claim_id: "googl-ironwood-cost-capacity",
      source_id: "google-ironwood",
      entity: "GOOGL",
      claim: "Ironwood supports the Google cost-control and NVIDIA-bypass thesis.",
      evidence_type: "company_product_page",
      metric: "seventh-generation TPU for inference-scale workloads",
      quote_or_excerpt: "Ironwood TPU inference positioning",
      retrieved_at: "2026-05-22",
      confidence: "High"
    },
    {
      claim_id: "avgo-custom-ai-accelerator",
      source_id: "broadcom-openai",
      entity: "AVGO",
      claim: "Broadcom has direct custom-accelerator exposure to hyperscaler AI infrastructure.",
      evidence_type: "company_press_release",
      metric: "10GW custom accelerator collaboration",
      quote_or_excerpt: "OpenAI/Broadcom strategic collaboration",
      retrieved_at: "2026-05-22",
      confidence: "High"
    },
    {
      claim_id: "nvda-rubin-platform",
      source_id: "nvidia-rubin",
      entity: "NVDA",
      claim: "Rubin NVL72 supports the rack-scale AI factory platform thesis.",
      evidence_type: "company_product_page",
      metric: "Rubin GPU, Vera CPU, NVLink, networking, DPU stack",
      quote_or_excerpt: "Rack-scale platform architecture",
      retrieved_at: "2026-05-22",
      confidence: "High"
    },
    {
      claim_id: "tsm-ai-capacity",
      source_id: "tsmc-transcript",
      entity: "TSM",
      claim: "AI demand remains a central driver of leading-edge capacity planning.",
      evidence_type: "company_transcript",
      metric: "AI demand and capacity commentary",
      quote_or_excerpt: "AI applications demand discussion",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "sk-hynix-hbm4",
      source_id: "skhynix-hbm4",
      entity: "000660.KS",
      claim: "SK hynix remains a direct HBM4 bottleneck exposure.",
      evidence_type: "company_press_release",
      metric: "HBM4 development and mass-production readiness",
      quote_or_excerpt: "HBM4 development completion",
      retrieved_at: "2026-05-22",
      confidence: "High"
    },
    {
      claim_id: "mu-hbm4-hbm4e-ramp",
      source_id: "micron-q2-2026-deck",
      entity: "MU",
      claim: "Micron's HBM4 and HBM4E roadmap is a credible watchlist catalyst but still needs durability proof.",
      evidence_type: "company_earnings_deck",
      metric: "HBM4 shipments, HBM4 16-high sampling, HBM4E 1-gamma roadmap",
      quote_or_excerpt: "Q2 2026 deck HBM roadmap disclosure",
      retrieved_at: "2026-05-24",
      confidence: "High"
    },
    {
      claim_id: "mu-sca-memory-re-rating",
      source_id: "micron-q2-2026-deck",
      entity: "MU",
      claim: "Micron's SCA language is the key test for whether memory demand is becoming more contracted.",
      evidence_type: "company_earnings_deck",
      metric: "strategic customer agreements",
      quote_or_excerpt: "Five-year SCA and multi-year commitment language",
      retrieved_at: "2026-05-24",
      confidence: "Medium"
    },
    {
      claim_id: "mu-gross-margin-watch",
      source_id: "micron-q2-2026-results",
      entity: "MU",
      claim: "Micron's FQ3 2026 gross-margin guide is a near-term durability watch item.",
      evidence_type: "company_earnings_release",
      metric: "FQ3 2026 gross margin guide",
      quote_or_excerpt: "Approximately 81% gross margin outlook",
      retrieved_at: "2026-05-24",
      confidence: "High"
    },
    {
      claim_id: "skhynix-high-na-euv-memory",
      source_id: "skhynix-high-na-euv",
      entity: "000660.KS",
      claim: "SK hynix's High-NA EUV installation supports its next-generation memory manufacturing thesis.",
      evidence_type: "company_press_release",
      metric: "High-NA EUV adoption for next-generation memory",
      quote_or_excerpt: "EXE:5200B assembled at M16 fab",
      retrieved_at: "2026-05-24",
      confidence: "High"
    },
    {
      claim_id: "ceg-pjm-interconnection-risk",
      source_id: "pjm-interconnection-process",
      entity: "CEG",
      claim: "Power thesis depends on interconnection and transmission process, not only generation assets.",
      evidence_type: "grid_process_documentation",
      metric: "interconnection request process",
      quote_or_excerpt: "PJM service request process",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "vrt-ai-power-cooling",
      source_id: "vertiv-trends",
      entity: "VRT",
      claim: "AI data-center design increases demand for high-density power and liquid cooling.",
      evidence_type: "company_industry_outlook",
      metric: "power and liquid cooling trend",
      quote_or_excerpt: "AI data-center design and operations trends",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "msci-retention-analytics",
      source_id: "msci-q1-2026",
      entity: "MSCI",
      claim: "MSCI has durable institutional workflow exposure, but verifier purity is partial.",
      evidence_type: "company_earnings_release",
      metric: "revenue growth and retention",
      quote_or_excerpt: "Q1 2026 operating results",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "mco-research-assistant",
      source_id: "moodys-research-assistant",
      entity: "MCO",
      claim: "Moody's Research Assistant maps closely to credit-risk verification workflows.",
      evidence_type: "company_product_page",
      metric: "entity screening, credit analysis, portfolio monitoring",
      quote_or_excerpt: "Research Assistant workflow positioning",
      retrieved_at: "2026-05-22",
      confidence: "High"
    },
    {
      claim_id: "spgi-kensho-agentic-data",
      source_id: "kensho-mcp",
      entity: "SPGI",
      claim: "Kensho gives S&P Global an AI retrieval path for trusted financial data.",
      evidence_type: "company_product_update",
      metric: "MCP server and LLM-ready data retrieval",
      quote_or_excerpt: "LLM-ready API and MCP server access",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "veev-regulated-agents",
      source_id: "veeva-ai-agents",
      entity: "VEEV",
      claim: "Veeva's AI Agents roadmap is a clean regulated-workflow trusted-execution proxy.",
      evidence_type: "company_product_roadmap",
      metric: "AI Agents across Veeva applications",
      quote_or_excerpt: "AI Agents release roadmap",
      retrieved_at: "2026-05-22",
      confidence: "Medium"
    },
    {
      claim_id: "ter-ai-semitest",
      source_id: "teradyne-q1-2026",
      entity: "TER",
      claim: "Teradyne's current AI exposure is primarily semiconductor test, not robotics.",
      evidence_type: "company_earnings_release",
      metric: "Semiconductor Test revenue versus Robotics revenue",
      quote_or_excerpt: "Q1 2026 segment results",
      retrieved_at: "2026-05-22",
      confidence: "High"
    }
  ],
  holdings: [
    {
      ticker: "MSFT",
      name: "Microsoft",
      weight: 18,
      bucket: "Core compounders",
      conviction: "A",
      layers: ["Authority", "Outcome"],
      confidence: "High",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "The cleanest public authority-control asset: identity, permissioning, observability, governance, and enterprise workflow distribution. Production write-permission adoption is the unproven variable.",
      evidence: [
        {
          id: "msft-evidence-agent365-governance-surface",
          text: "Agent 365 gives Microsoft a concrete product surface for agent governance.",
          materiality: "high",
          claim_ids: ["msft-agent-authority"],
          metric_ids: ["agent_governance_evidence"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "msft-evidence-security-agent-governance",
          text: "Microsoft security materials emphasize observing, governing, and securing agent activity.",
          materiality: "high",
          claim_ids: ["msft-agent-authority"],
          metric_ids: ["security_attach", "agent_governance_evidence"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "Entra, Defender, Microsoft 365, GitHub, and Azure create a stacked authority layer, but adoption depth must be measured."
      ],
      risks: ["Trust plateau", "Regulatory pressure", "Premium valuation"],
      falsifier: "Enterprise agents remain draft-only and fail to gain production write permissions by 2027.",
      watch: "Agent 365 adoption with real write permissions, not just draft-and-approve usage.",
      sources: ["msft-agent365", "msft-security-agent365"]
    },
    {
      ticker: "GOOGL",
      name: "Alphabet",
      weight: 15,
      bucket: "Core compounders",
      conviction: "A-",
      layers: ["Capacity", "Cost", "Authority", "Outcome"],
      confidence: "High",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "The strongest NVIDIA-bypass path: custom TPU infrastructure, DeepMind, Workspace distribution, Search cash flow, and Google Cloud.",
      evidence: [
        {
          id: "googl-evidence-ironwood-inference-tpu",
          text: "Ironwood is Google's seventh-generation TPU and is designed for inference-scale AI workloads.",
          materiality: "high",
          claim_ids: ["googl-ironwood-cost-capacity"],
          metric_ids: ["tpu_product_evidence"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "googl-evidence-tpu-cost-internalization",
          text: "Google can internalize cost control through TPU deployment while still selling cloud AI capacity.",
          materiality: "high",
          claim_ids: ["googl-ironwood-cost-capacity"],
          metric_ids: ["google_cloud_revenue_margin", "tpu_product_evidence"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "Workspace and Cloud give Google a route into enterprise authority and workflow; production authority adoption remains a watch item."
      ],
      risks: ["Search disruption", "Regulatory pressure", "Capex ROI uncertainty"],
      falsifier: "TPU cost advantage fails to appear in Cloud margins, AI revenue quality, or external demand.",
      watch: "AI revenue growth versus capex intensity, Cloud margins, and TPU external demand.",
      sources: ["google-ironwood", "google-ironwood-3things"]
    },
    {
      ticker: "AVGO",
      name: "Broadcom",
      weight: 10,
      bucket: "Core compounders",
      conviction: "A-",
      layers: ["Capacity", "Cost"],
      confidence: "Medium-high",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Custom silicon and AI networking proxy for hyperscaler internalization of accelerator economics.",
      evidence: [
        {
          id: "avgo-evidence-ai-semiconductor-demand",
          text: "Broadcom reported strong AI semiconductor demand in fiscal Q1 2026.",
          materiality: "high",
          claim_ids: ["avgo-custom-ai-accelerator"],
          metric_ids: ["ai_semiconductor_revenue"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "avgo-evidence-openai-custom-accelerator",
          text: "OpenAI and Broadcom announced a 10GW custom accelerator collaboration.",
          materiality: "high",
          claim_ids: ["avgo-custom-ai-accelerator"],
          metric_ids: ["xpu_customer_count"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "avgo-evidence-meta-custom-infrastructure",
          text: "Broadcom and Meta extended a custom AI infrastructure partnership around MTIA and networking.",
          materiality: "high",
          claim_ids: ["avgo-custom-ai-accelerator"],
          metric_ids: ["xpu_customer_count", "networking_attach_rate"],
          evidence_state_source: "data/evidence_log.yml"
        }
      ],
      risks: ["Customer concentration", "ASIC program lumpiness", "VMware integration execution"],
      falsifier: "AI semiconductor growth slows while hyperscalers insource away from Broadcom.",
      watch: "AI semiconductor revenue, XPU customer count, and networking attach rate.",
      sources: ["broadcom-q1-2026", "broadcom-openai", "broadcom-meta"]
    },
    {
      ticker: "NVDA",
      name: "NVIDIA",
      weight: 7,
      bucket: "Core compounders",
      conviction: "A-",
      layers: ["Capacity", "Cost"],
      confidence: "Medium-high",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Still the AI factory operating layer, not a commodity GPU vendor. The position is sized below hyperscaler/custom-silicon winners but above a token hedge.",
      evidence: [
        {
          id: "nvda-evidence-rubin-nvl72-stack",
          text: "Vera Rubin NVL72 integrates Rubin GPUs, Vera CPUs, NVLink 6, ConnectX-9, and BlueField-4.",
          materiality: "high",
          claim_ids: ["nvda-rubin-platform"],
          metric_ids: ["networking_attach"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "nvda-evidence-rack-scale-template",
          text: "The rack-scale architecture turns NVIDIA into a deployment template for AI factories.",
          materiality: "high",
          claim_ids: ["nvda-rubin-platform"],
          metric_ids: ["networking_attach", "rubin_blackwell_shipments"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "The moat is system design, fabric, software, ecosystem, and time-to-deploy; monetization durability must be tracked separately."
      ],
      risks: ["Custom silicon bypass", "Margin compression", "Export controls"],
      falsifier: "Rubin racks ship, but networking attach, software pull-through, and margins compress sharply.",
      watch:
        "Rubin delivery cadence, NVL rack adoption, networking attach rate, data-center gross margin, and bypass share.",
      sources: ["nvidia-rubin", "nvidia-rubin-blog"]
    },
    {
      ticker: "TSM",
      name: "TSMC",
      weight: 7,
      bucket: "Core compounders",
      conviction: "B+",
      layers: ["Capacity"],
      confidence: "Medium-high",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "A leading-edge foundry and advanced packaging chokepoint, but not a direct authority or outcome-control asset.",
      evidence: [
        {
          id: "tsm-evidence-q1-2026-margin-delivery",
          text: "TSMC's Q1 2026 investor page shows strong revenue and margin delivery.",
          materiality: "high",
          claim_ids: ["tsm-ai-capacity"],
          metric_ids: ["gross_margin"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "tsm-evidence-ai-capacity-planning",
          text: "TSMC transcripts continue to frame AI as a multi-year demand and capacity-planning driver.",
          materiality: "high",
          claim_ids: ["tsm-ai-capacity"],
          metric_ids: ["hpc_revenue_mix"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "Advanced process and advanced packaging capacity remain central to AI silicon scaling."
      ],
      risks: ["Geopolitics", "Capex cycle", "Overseas fab cost"],
      falsifier: "Advanced packaging scarcity resolves faster than expected or geopolitics/cost overwhelm the moat.",
      watch: "N3/N2 demand, CoWoS capacity, HPC mix, and gross margin through capex ramp.",
      sources: ["tsmc-q1-2026", "tsmc-transcript"]
    },
    {
      ticker: "000660.KS",
      name: "SK Hynix",
      weight: 8,
      bucket: "Bottleneck cyclicals",
      conviction: "B+",
      layers: ["Capacity"],
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "HBM4 leadership exposure, with explicit quarterly review of Samsung and Micron qualification risk.",
      evidence: [
        {
          id: "skhynix-evidence-hbm4-readiness",
          text: "SK hynix announced HBM4 development completion and mass-production readiness.",
          materiality: "high",
          claim_ids: ["sk-hynix-hbm4"],
          metric_ids: ["hbm_revenue_commentary"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "skhynix-evidence-high-value-hbm-products",
          text: "Q1 2026 results cite high-value products including HBM, server DRAM, and eSSDs.",
          materiality: "high",
          claim_ids: ["sk-hynix-hbm4"],
          metric_ids: ["hbm_revenue_commentary", "dram_price_cycle"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "HBM is a bottleneck, but it remains a memory-cycle and qualification-cycle asset."
      ],
      risks: ["Memory cycle", "Customer concentration", "Samsung HBM4 comeback"],
      falsifier: "Samsung or Micron exceeds 30% Rubin-generation HBM share and HBM pricing power normalizes.",
      watch: "NVIDIA qualification, HBM4E roadmap, HBM pricing, and Samsung sample progress.",
      sources: ["skhynix-hbm4", "skhynix-q1-2026"]
    },
    {
      ticker: "CEG",
      name: "Constellation Energy",
      weight: 5,
      bucket: "Bottleneck cyclicals",
      conviction: "B",
      layers: ["Capacity"],
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "High-quality but interconnection-heavy nodal power exposure, not a generic power thesis.",
      evidence: [
        {
          id: "ceg-evidence-tmi-pjm-delay",
          text: "The Three Mile Island / PJM delay shows the bottleneck is grid connection, transmission, and regulator timing.",
          materiality: "high",
          claim_ids: ["ceg-pjm-interconnection-risk"],
          metric_ids: ["pjm_interconnection"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "ceg-evidence-pjm-monitoring-layer",
          text: "PJM interconnection process data is a required monitoring layer for node-level power underwriting.",
          materiality: "high",
          claim_ids: ["ceg-pjm-interconnection-risk"],
          metric_ids: ["pjm_interconnection"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "The position was reduced to reflect consensus power enthusiasm and project-level uncertainty.",
        "Nuclear PPAs still matter, but node underwriting matters more."
      ],
      risks: ["Transmission delay", "Regulatory timing", "Power price volatility"],
      falsifier: "TMI delay persists, interconnection bottlenecks worsen, or data-center PPAs fail to convert into earnings.",
      watch: "PJM interconnection queues, node-level PPA economics, and data-center site constraints.",
      sources: ["ceg-tmi-pjm", "pjm-interconnection-process"]
    },
    {
      ticker: "VRT",
      name: "Vertiv",
      weight: 5,
      bucket: "Bottleneck cyclicals",
      conviction: "B",
      layers: ["Capacity"],
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Clean data-center power and thermal infrastructure exposure, with explicit capex-cycle beta.",
      evidence: [
        {
          id: "vrt-evidence-high-density-power-cooling",
          text: "Vertiv highlights high-density power and liquid cooling as central to AI data-center design.",
          materiality: "high",
          claim_ids: ["vrt-ai-power-cooling"],
          metric_ids: ["liquid_cooling_commentary"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "vrt-evidence-generate-power-constrained-markets",
          text: "The Generate Capital collaboration targets power-constrained markets with power and cooling infrastructure.",
          materiality: "high",
          claim_ids: ["vrt-ai-power-cooling"],
          metric_ids: ["orders_backlog", "liquid_cooling_commentary"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "The company is a picks-and-shovels beneficiary, not a closed-loop control-right owner."
      ],
      risks: ["Hyperscaler capex crack", "Execution", "Valuation"],
      falsifier: "Hyperscaler capex pauses and Vertiv backlog quality or liquid-cooling demand deteriorates.",
      watch: "Order growth, backlog quality, liquid cooling capacity, and hyperscaler capex guidance.",
      sources: ["vertiv-trends", "vertiv-generate"]
    },
    {
      ticker: "MSCI",
      name: "MSCI",
      weight: 2,
      bucket: "Vertical verifier basket",
      conviction: "B",
      layers: ["Outcome"],
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Financial data, index, and risk analytics control point. Good outcome-adjacent proxy, but less pure than ratings or life-sciences workflow verifiers.",
      evidence: [
        {
          id: "msci-evidence-q1-retention-analytics",
          text: "MSCI reported Q1 2026 revenue growth and high retention.",
          materiality: "high",
          claim_ids: ["msci-retention-analytics"],
          metric_ids: ["recurring_subscription_growth", "retention"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "The data and index franchise remains embedded in institutional workflow.",
        "Basket sizing acknowledges that no single public name perfectly captures vertical verification; retention and analytics run-rate are the measurable bridge."
      ],
      risks: ["Market-cycle asset fees", "Outcome-verifier purity", "Valuation"],
      falsifier: "AI analytics adoption fails to affect retention, pricing, or analytics run-rate.",
      watch:
        "Retention, subscription run-rate growth, analytics run-rate, and AI-enabled analytics adoption.",
      sources: ["msci-q1-2026"]
    },
    {
      ticker: "MCO",
      name: "Moody's",
      weight: 2,
      bucket: "Vertical verifier basket",
      conviction: "B+",
      layers: ["Outcome"],
      confidence: "Medium-high",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Credit-risk verifier with proprietary data, ratings context, and AI decision-intelligence products.",
      evidence: [
        {
          id: "mco-evidence-research-assistant-workflows",
          text: "Moody's Research Assistant targets entity screening, credit analysis, and portfolio monitoring.",
          materiality: "high",
          claim_ids: ["mco-research-assistant"],
          metric_ids: ["research_assistant_adoption"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "Moody's describes GenAI products as grounded in proprietary data and risk expertise.",
        "The verifier angle is more direct than generic financial data exposure."
      ],
      risks: ["Credit cycle", "Regulatory scrutiny", "Ratings volume volatility"],
      falsifier: "AI tools do not improve analytics growth, customer workflow depth, or monitoring usage.",
      watch:
        "Analytics revenue, Research Assistant adoption, disclosed AI usage, and credit-cycle sensitivity.",
      sources: ["moodys-research-assistant", "moodys-genai"]
    },
    {
      ticker: "SPGI",
      name: "S&P Global",
      weight: 2,
      bucket: "Vertical verifier basket",
      conviction: "B+",
      layers: ["Outcome"],
      confidence: "Medium-high",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Ratings and data-verifier exposure with Kensho as an AI retrieval and financial-workflow layer.",
      evidence: [
        {
          id: "spgi-evidence-kensho-llm-data",
          text: "Kensho connects LLMs and agents to S&P Global's trusted data.",
          materiality: "high",
          claim_ids: ["spgi-kensho-agentic-data"],
          metric_ids: ["kensho_api_mcp_mentions"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "spgi-evidence-kensho-mcp-server",
          text: "Kensho expanded MCP server support for LLM-ready data retrieval.",
          materiality: "high",
          claim_ids: ["spgi-kensho-agentic-data"],
          metric_ids: ["kensho_api_mcp_mentions"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "S&P AI Benchmarks by Kensho target business and financial use cases."
      ],
      risks: ["Ratings cyclicality", "Data licensing competition", "AI product monetization timing"],
      falsifier: "Kensho MCP/API usage remains narrative and does not show up in revenue, retention, or workflow adoption.",
      watch:
        "Kensho revenue contribution, MCP/API usage, data-retrieval integrations, and AI benchmark adoption.",
      sources: ["kensho-home", "kensho-mcp", "spgi-ai"]
    },
    {
      ticker: "VEEV",
      name: "Veeva Systems",
      weight: 2,
      bucket: "Vertical verifier basket",
      conviction: "B+",
      layers: ["Outcome"],
      confidence: "Medium-high",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Life-sciences workflow verifier where agentic AI can operate inside regulated applications and data.",
      evidence: [
        {
          id: "veev-evidence-ai-agents-roadmap",
          text: "Veeva plans AI Agents across commercial, clinical, regulatory, safety, quality, medical, and data applications.",
          materiality: "high",
          claim_ids: ["veev-regulated-agents"],
          metric_ids: ["ai_agents_rollout"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "veev-evidence-agent-safeguards-context",
          text: "Veeva emphasizes application context, safeguards, and secure access to application data and workflows.",
          materiality: "high",
          claim_ids: ["veev-regulated-agents"],
          metric_ids: ["ai_agents_rollout"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "This is one of the cleaner public proxies for domain-specific trusted execution."
      ],
      risks: ["Life-sciences IT cycle", "Product rollout timing", "Regulated customer adoption"],
      falsifier: "AI Agents stay roadmap-only or show low usage across regulated workflows.",
      watch:
        "Agent rollout milestones, Vault CRM migration, regulated workflow automation evidence, and customer adoption disclosures.",
      sources: ["veeva-ai-agents"]
    },
    {
      ticker: "TER",
      name: "Teradyne",
      weight: 7,
      bucket: "Asymmetric optionality",
      conviction: "B",
      layers: ["Capacity", "Physical AI"],
      confidence: "Medium",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "AI semiconductor test cycle core exposure plus robotics optionality, not a pure humanoid play.",
      evidence: [
        {
          id: "ter-evidence-semitest-primary-exposure",
          text: "Teradyne Q1 2026 revenue was driven mostly by Semiconductor Test, not Robotics.",
          materiality: "high",
          claim_ids: ["ter-ai-semitest"],
          metric_ids: ["semiconductor_test_revenue"],
          evidence_state_source: "data/evidence_log.yml"
        },
        {
          id: "ter-evidence-ai-related-revenue",
          text: "Management tied about 70% of revenue to AI-related demand.",
          materiality: "high",
          claim_ids: ["ter-ai-semitest"],
          metric_ids: ["semiconductor_test_revenue"],
          evidence_state_source: "data/evidence_log.yml"
        },
        "Flex and Teradyne Robotics expanded collaboration for intelligent manufacturing automation."
      ],
      risks: ["Semitest digestion", "Robotics execution", "Project-based demand lumpiness"],
      falsifier: "AI semiconductor-test demand normalizes before robotics can become material.",
      watch: "Semiconductor Test bookings, memory/compute test exposure, and robotics attach to AI factories.",
      sources: ["teradyne-q1-2026", "teradyne-flex"]
    },
    {
      ticker: "CASH",
      name: "Cash",
      weight: 10,
      bucket: "Dry powder",
      conviction: "Policy",
      layers: ["Risk control"],
      confidence: "Policy",
      last_reviewed_at: "2026-05-22",
      next_review_due: "2026-08-22",
      thesis:
        "Option value for capex narrative cracks, regulatory shocks, or framework-level regime changes.",
      evidence: [
        "Risk and tail scenarios are intentionally non-zero.",
        "Cash is a strategic asset when the framework is young and indicator history is thin.",
        "The system suggests deploying cash only after review, not automatically."
      ],
      risks: ["Cash drag", "Inflation", "Opportunity cost"],
      falsifier: "Framework remains valid, valuations never reset, and cash drag becomes the dominant portfolio error.",
      watch: "Drawdown plus VIX stress, plateau alerts, and valuation reset opportunities.",
      sources: []
    }
  ],
  sources: {
    "metr-home": {
      label: "METR time-horizon research hub",
      url: "https://metr.org/index.html"
    },
    "metr-long-tasks": {
      label: "METR paper - Measuring AI Ability to Complete Long Software Tasks",
      url: "https://arxiv.org/abs/2503.14499"
    },
    "epoch-inference-prices": {
      label: "Epoch AI - LLM inference price trends",
      url: "https://epoch.ai/data-insights/llm-inference-price-trends"
    },
    "openai-swebench": {
      label: "OpenAI - SWE-bench Verified limitations",
      url: "https://openai.com/index/why-we-no-longer-evaluate-swe-bench-verified/"
    },
    "mcp-tools-arxiv": {
      label: "MCP tools usage paper",
      url: "https://arxiv.org/abs/2603.23802"
    },
    "msft-agent365": {
      label: "Microsoft Agent 365",
      url: "https://www.microsoft.com/microsoft-agent-365"
    },
    "msft-security-agent365": {
      label: "Microsoft Security Blog - Agent 365 GA",
      url: "https://www.microsoft.com/en-us/security/blog/2026/05/01/microsoft-agent-365-now-generally-available-expands-capabilities-and-integrations/"
    },
    "google-ironwood": {
      label: "Google - Ironwood TPU for inference",
      url: "https://blog.google/products/google-cloud/ironwood-tpu-age-of-inference/"
    },
    "google-ironwood-3things": {
      label: "Google - Three things about Ironwood",
      url: "https://blog.google/products/google-cloud/ironwood-google-tpu-things-to-know/"
    },
    "nvidia-rubin": {
      label: "NVIDIA Vera Rubin NVL72",
      url: "https://www.nvidia.com/en-us/data-center/vera-rubin-nvl72/"
    },
    "nvidia-rubin-blog": {
      label: "NVIDIA Technical Blog - Vera Rubin Platform",
      url: "https://developer.nvidia.com/blog/inside-the-nvidia-rubin-platform-six-new-chips-one-ai-supercomputer/"
    },
    "broadcom-q1-2026": {
      label: "Broadcom Q1 FY2026 results",
      url: "https://investors.broadcom.com/node/63976/pdf"
    },
    "broadcom-openai": {
      label: "OpenAI and Broadcom 10GW collaboration",
      url: "https://investors.broadcom.com/news-releases/news-release-details/openai-and-broadcom-announce-strategic-collaboration-deploy-10"
    },
    "broadcom-meta": {
      label: "Broadcom and Meta partnership",
      url: "https://investors.broadcom.com/node/64236/pdf"
    },
    "tsmc-q1-2026": {
      label: "TSMC Q1 2026 quarterly results",
      url: "https://investor.tsmc.com/english/quarterly-results"
    },
    "tsmc-transcript": {
      label: "TSMC Q1 2026 transcript",
      url: "https://investor.tsmc.com/english/encrypt/files/encrypt_file/reports/2026-04/3cef85204275f94fd111485cfdf4adb3c0263c45/TSMC%201Q26%20Transcript.pdf"
    },
    "skhynix-hbm4": {
      label: "SK hynix HBM4 development",
      url: "https://news.skhynix.com/sk-hynix_sk-hynix-completes-worlds-first-hbm4-development-and-readies-mass-production_01/"
    },
    "skhynix-q1-2026": {
      label: "SK hynix Q1 2026 results",
      url: "https://news.skhynix.com/q1-2026-business-results/"
    },
    "skhynix-fy2025-results": {
      label: "SK hynix FY2025 results",
      url: "https://news.skhynix.com/sk-hynix-announces-fy25-financial-results/"
    },
    "skhynix-high-na-euv": {
      label: "SK hynix High-NA EUV installation",
      url: "https://news.skhynix.com/sk-hynix-introduces-industrys-first-commercial-high-na-euv/"
    },
    "micron-q2-2026-results": {
      label: "Micron Q2 FY2026 results",
      url: "https://investors.micron.com/news-releases/news-release-details/micron-technology-inc-reports-results-second-quarter-fiscal-2026"
    },
    "micron-q2-2026-deck": {
      label: "Micron Q2 FY2026 earnings deck",
      url: "https://investors.micron.com/static-files/9c0becf5-df56-4eec-bd67-453dda68b273"
    },
    "micron-jpm-2026": {
      label: "Micron 2026 J.P. Morgan TMT event",
      url: "https://investors.micron.com/events/event-details/2026-jp-morgan-global-technology-media-and-communications-conference"
    },
    "micron-sec-submissions": {
      label: "SEC submissions - Micron Technology",
      url: "https://data.sec.gov/submissions/CIK0000723125.json"
    },
    "asml-2025-results": {
      label: "ASML FY2025 results",
      url: "https://www.asml.com/en/news/press-releases/2026/q4-2025-financial-results"
    },
    "ceg-tmi-pjm": {
      label: "Reuters via Investing.com - Three Mile Island PJM delay",
      url: "https://www.investing.com/news/stock-market-news/constellation-exec-says-grid-operator-told-company-three-mile-island-cant-connect-until-2031-4583367"
    },
    "pjm-interconnection-process": {
      label: "PJM interconnection request process",
      url: "https://www.pjm.com/planning/service-requests/application-and-forms"
    },
    "vertiv-trends": {
      label: "Vertiv 2026 AI data-center trends",
      url: "https://www.vertiv.com/en-us/about/news-and-insights/corporate-news/vertiv-expects-powering-up-for-ai-digital-twins-and-adaptive-liquid-cooling-to-shape-data-center-design-and-operations/"
    },
    "vertiv-generate": {
      label: "Vertiv and Generate Capital BYOP&C",
      url: "https://investors.vertiv.com/news/news-details/2026/Vertiv-and-Generate-Capital-Collaborate-to-Accelerate-Data-Center-Capacity-with-Complete-Power-and-Cooling-Infrastructure/"
    },
    "msci-q1-2026": {
      label: "MSCI Q1 2026 results",
      url: "https://ir.msci.com/news-releases/news-release-details/msci-reports-financial-results-first-quarter-2026"
    },
    "moodys-research-assistant": {
      label: "Moody's Research Assistant",
      url: "https://www.moodys.com/web/en/us/research-assistant.html"
    },
    "moodys-genai": {
      label: "Moody's AI and GenAI capabilities",
      url: "https://www.moodys.com/web/en/us/capabilities/gen-ai.html"
    },
    "kensho-home": {
      label: "Kensho - S&P Global AI engine",
      url: "https://kensho.com/"
    },
    "kensho-mcp": {
      label: "Kensho LLM-ready API and MCP server",
      url: "https://kensho.com/news/kensho-llm-ready-api-expands-mcp-server-access-dataset-support-integrations"
    },
    "spgi-ai": {
      label: "S&P Global AI insights and benchmarks",
      url: "https://www.spglobal.com/en/research-insights/market-insights/artificial-intelligence"
    },
    "veeva-ai-agents": {
      label: "Veeva AI Agents roadmap",
      url: "https://www.veeva.com/eu/resources/veeva-ai-agents-to-be-released-across-all-veeva-applications/"
    },
    "teradyne-q1-2026": {
      label: "Teradyne Q1 2026 results",
      url: "https://investors.teradyne.com/news-events/press-releases/detail/440/teradyne-reports-first-quarter-2026-results"
    },
    "teradyne-flex": {
      label: "Flex and Teradyne Robotics partnership",
      url: "https://www.universal-robots.com/news-and-media/news-center/flex-teradyne-robotics-expand-partnership-scale-intelligent-automation-across-global-manufacturing/"
    }
  }
};
