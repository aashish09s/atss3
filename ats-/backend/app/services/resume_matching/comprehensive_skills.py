"""
Comprehensive Skills Database for Resume Matching System

This module contains all the skill sets, job profiles, and certifications
organized by categories for enhanced resume analysis and job matching.
"""

from typing import Dict, List, Any

# Comprehensive Skills Database
COMPREHENSIVE_SKILLS = {
    "engineering_software_qa": [
        "python", "java", "c++", "c#", "javascript", "typescript", "go", "ruby", "php", "swift", "kotlin", 
        "scala", "react", "angular", "vue", "svelte", "next.js", "tailwind css", "bootstrap", "material-ui", 
        "html", "css", "node.js", "express", "django", "flask", "spring", "fastapi", "asp.net", "laravel", 
        "graphql", "rest api", "sql", "mysql", "postgresql", "mongodb", "oracle", "sql server", "redis", 
        "elasticsearch", "cassandra", "aws", "azure", "gcp", "docker", "kubernetes", "terraform", "jenkins", 
        "github actions", "gitlab ci", "agile", "scrum", "tdd", "bdd", "design patterns", "clean architecture", 
        "solid principles", "selenium", "cypress", "playwright", "pytest", "junit", "testng", "cucumber", 
        "robot framework", "performance testing", "load testing", "security testing", "integration testing", 
        "api testing"
    ],

    "sales_business_development": [
        "lead generation", "prospecting", "cold calling", "email outreach", "crm", "salesforce", 
        "hubspot crm", "zoho crm", "pipedrive", "microsoft dynamics", "negotiation", "deal closing", 
        "presentation skills", "solution selling", "consultative selling", "b2b sales", "b2c sales", 
        "sales pipeline management", "forecasting", "territory management", "account management", 
        "upselling", "cross-selling", "objection handling", "social selling", "linkedin sales navigator", 
        "data-driven sales", "kpi tracking", "sales analytics", "pricing strategies", "market research", 
        "competitive analysis", "sales enablement", "channel sales", "partner management", "enterprise sales", 
        "retail sales", "inside sales", "field sales"
    ],

    "data_science_analytics": [
        "python", "r", "sql", "excel", "tableau", "power bi", "lookerstudio", "pandas", "numpy", 
        "scikit-learn", "tensorflow", "pytorch", "keras", "matplotlib", "seaborn", "plotly", 
        "statistics", "probability", "linear regression", "logistic regression", "decision trees", 
        "random forests", "xgboost", "catboost", "nlp", "computer vision", "deep learning", 
        "feature engineering", "model deployment", "mlops", "airflow", "mlflow", "databricks", 
        "bigquery", "snowflake", "hive", "spark", "hadoop", "data cleaning", "data wrangling", 
        "data preprocessing", "a/b testing", "time series forecasting", "predictive modeling", 
        "business analytics"
    ],

    "human_resources": [
        "onboarding", "offboarding", "payroll", "compliance", "hr policies", "employee engagement", 
        "performance management", "succession planning", "talent acquisition", "recruitment", 
        "linkedin recruiter", "boolean search", "greenhouse", "lever", "workday", "sap successfactors", 
        "oracle hcm", "bamboohr", "employee relations", "training and development", "e-learning platforms", 
        "diversity and inclusion", "workforce planning", "conflict resolution", "hr analytics", 
        "employee surveys", "360 feedback", "benefits administration", "time tracking", "hr dashboards", 
        "labor law compliance", "background checks"
    ],

    "marketing_communication": [
        "seo", "sem", "google analytics", "google ads", "meta ads", "ppc", "content marketing", 
        "copywriting", "storytelling", "email marketing", "mailchimp", "hubspot", "social media marketing", 
        "instagram marketing", "linkedin marketing", "youtube campaigns", "influencer marketing", 
        "branding", "digital strategy", "consumer psychology", "a/b testing", "conversion rate optimization", 
        "video marketing", "pr campaigns", "press releases", "public speaking", "market research", 
        "blogging", "wordpress", "webflow", "canva", "adobe photoshop", "adobe illustrator", 
        "after effects", "communication strategy"
    ]
}

# Additional Skills Categories
ADDITIONAL_SKILLS = {
    "consulting": [
        "management consulting", "strategy consulting", "it consulting", "financial consulting", 
        "operations consulting", "supply chain consulting", "digital transformation", 
        "business process reengineering", "market entry strategy", "competitive analysis", 
        "data-driven decision making", "change management", "stakeholder management", 
        "business model design", "roi analysis", "project scoping", "risk assessment", 
        "business case development", "lean six sigma", "kaizen", "agile transformation", 
        "performance benchmarking", "process optimization", "vendor management", 
        "cost reduction strategy", "mergers and acquisitions", "organizational development", 
        "erp consulting", "sap", "oracle erp", "salesforce consulting"
    ],

    "customer_success_service_operations": [
        "customer onboarding", "customer support", "ticketing systems", "zendesk", "freshdesk", 
        "intercom", "salesforce service cloud", "crm management", "client relationship management", 
        "sla management", "kpi tracking", "customer health scoring", "churn analysis", 
        "net promoter score (nps)", "csat", "customer journey mapping", "renewals management", 
        "upselling", "cross-selling", "knowledge base management", "faq automation", 
        "chatbots", "live chat support", "omnichannel support", "call center operations", 
        "ivr systems", "service desk", "problem resolution", "customer retention strategies", 
        "community management", "customer advocacy"
    ],

    "it_information_security": [
        "network security", "application security", "cloud security", "data security", "endpoint security", 
        "identity and access management (iam)", "single sign-on (sso)", "multi-factor authentication", 
        "firewalls", "intrusion detection systems", "intrusion prevention systems", "vpn", 
        "siem", "splunk", "elk stack", "qradar", "threat intelligence", "penetration testing", 
        "ethical hacking", "vulnerability assessment", "incident response", "forensics", 
        "risk management", "iso 27001", "nist framework", "gdpr compliance", "hipaa compliance", 
        "pci dss", "soc 2", "cloudflare", "aws security hub", "azure security center", 
        "gcp security command center", "wireshark", "metasploit", "burp suite", "owasp top 10", 
        "zero trust architecture"
    ],

    "content_editorial_journalism": [
        "content writing", "copywriting", "technical writing", "creative writing", 
        "editing", "proofreading", "fact-checking", "journalistic ethics", "news reporting", 
        "feature writing", "op-ed writing", "interviewing", "investigative journalism", 
        "digital journalism", "seo writing", "content strategy", "wordpress", "medium", 
        "webflow", "cms management", "social media content", "linkedin posts", "newsletter creation", 
        "substack", "storytelling", "brand voice", "editorial calendar management", "headline writing", 
        "ap style", "chicago manual of style", "apa style", "long-form content", "short-form content", 
        "press releases", "video scripts", "podcast scripts", "blogging", "ghostwriting"
    ],

    "ux_design_architecture": [
        "user research", "user personas", "journey mapping", "wireframing", "prototyping", 
        "figma", "sketch", "adobe xd", "invision", "balsamiq", "axure rp", "zeplin", 
        "ui design", "responsive design", "mobile-first design", "design systems", 
        "material design", "ant design", "bootstrap", "tailwind css", "usability testing", 
        "a/b testing", "heuristic evaluation", "interaction design", "motion design", 
        "information architecture", "card sorting", "sitemaps", "accessibility (wcag)", 
        "color theory", "typography", "visual hierarchy", "human-computer interaction", 
        "3d design", "ar/vr interfaces", "game ui design"
    ],

    "teaching_training": [
        "curriculum design", "lesson planning", "instructional design", "e-learning", 
        "moodle", "blackboard", "canvas lms", "google classroom", "edmodo", 
        "student assessment", "rubrics", "learning outcomes", "pedagogy", 
        "andragogy", "classroom management", "blended learning", "flipped classroom", 
        "public speaking", "presentation skills", "educational technology", 
        "kahoot", "quizizz", "gamification", "adaptive learning", "virtual labs", 
        "ai in education", "student engagement", "online teaching", "zoom", 
        "microsoft teams", "webex", "training delivery", "corporate training", 
        "soft skills training", "technical training", "language training"
    ],

    "finance_accounting": [
        "financial reporting", "accounting standards", "ifrs", "gaap", "sap fico", 
        "oracle financials", "quickbooks", "tally", "xero", "microsoft dynamics 365 finance", 
        "auditing", "internal controls", "taxation", "gst", "vat", "income tax", 
        "financial modeling", "valuation", "budgeting", "forecasting", "variance analysis", 
        "cost accounting", "management accounting", "accounts payable", "accounts receivable", 
        "reconciliation", "treasury management", "cash flow analysis", "investment accounting", 
        "equity research", "credit risk analysis", "hedge accounting", "portfolio management", 
        "financial regulations", "sec compliance", "sox compliance"
    ],

    "project_program_management": [
        "project planning", "scope management", "risk management", "project scheduling", 
        "work breakdown structure", "pmi pmp", "prince2", "scrum", "kanban", "agile", 
        "jira", "asana", "trello", "microsoft project", "smartsheet", "confluence", 
        "stakeholder management", "resource allocation", "budgeting", "cost control", 
        "earned value management", "critical path method", "gantt charts", 
        "project documentation", "project governance", "program portfolio management", 
        "change management", "business case preparation", "project closure", 
        "lessons learned", "quality management", "six sigma in projects"
    ],

    "engineering_hardware_networks": [
        "computer architecture", "microprocessors", "embedded systems", "fpga programming", 
        "vhdl", "verilog", "pcb design", "altium designer", "eagle cad", "proteus", 
        "arduino", "raspberry pi", "iot hardware", "sensor integration", 
        "network design", "routing", "switching", "tcp/ip", "dns", "dhcp", "vpn", 
        "firewalls", "cisco ios", "juniper networks", "network security", "wireless networking", 
        "lan", "wan", "sd-wan", "network troubleshooting", "wireshark", "packet tracer", 
        "linux networking", "server administration", "vmware", "hyper-v"
    ],

    "healthcare_life_sciences": [
        "clinical research", "clinical trials", "gcp compliance", "fda regulations", 
        "medical writing", "regulatory affairs", "pharmacovigilance", "drug safety", 
        "biostatistics", "sas programming", "r for clinical data", "epidemiology", 
        "public health", "laboratory techniques", "molecular biology", "genomics", 
        "proteomics", "cell culture", "microscopy", "immunology", "toxicology", 
        "health informatics", "ehr systems", "epic systems", "cerner", "telemedicine", 
        "medical imaging", "radiology systems", "hipaa compliance", "clinical data management", 
        "medical coding", "icd-10", "cpt coding", "hl7 standards", "fhir standards"
    ],

    "construction_site_engineering": [
        "civil engineering", "structural engineering", "autocad", "revit", "staad pro", 
        "primavera p6", "ms project", "construction management", "site supervision", 
        "quantity surveying", "estimation", "bim", "construction safety", "osha compliance", 
        "cost control", "contract management", "tendering", "procurement", "material management", 
        "project scheduling", "site inspection", "quality control", "construction drawings", 
        "surveying", "total station", "gps surveying", "geotechnical engineering", "foundation design", 
        "concrete technology", "steel structures", "mep coordination"
    ],

    "production_manufacturing_engineering": [
        "lean manufacturing", "six sigma", "kaizen", "just in time (jit)", "tpm", 
        "autocad", "solidworks", "catia", "creo", "ansys", "process engineering", 
        "industrial engineering", "plant layout design", "production planning", 
        "quality management", "iso 9001", "supply chain coordination", "erp systems", 
        "sap pp", "oracle manufacturing cloud", "inventory management", 
        "automation", "robotics", "plc programming", "scada", "mes systems", 
        "safety compliance", "osha standards", "statistical process control", 
        "value stream mapping", "capacity planning"
    ],

    "product_management": [
        "product strategy", "roadmapping", "market research", "competitive analysis", 
        "customer journey mapping", "design thinking", "mvp development", "agile product management", 
        "scrum", "kanban", "jira", "confluence", "trello", "product lifecycle management", 
        "stakeholder management", "pricing strategy", "go-to-market strategy", 
        "a/b testing", "user research", "product analytics", "mixpanel", "amplitude", 
        "google analytics", "data-driven decision making", "okrs", "kpis", 
        "wireframing", "prototyping", "figma", "adobe xd", "roadmap prioritization"
    ],

    "research_development": [
        "literature review", "hypothesis testing", "data collection", "statistical analysis", 
        "experimental design", "r&d project management", "innovation management", 
        "patent search", "intellectual property", "technology scouting", "prototyping", 
        "lab experimentation", "simulation", "matlab", "comsol multiphysics", "ansys", 
        "chemistry research", "biological research", "material science", "nanotechnology", 
        "ai research", "ml research", "deep learning models", "algorithm development", 
        "scientific writing", "peer-reviewed publishing", "grant writing", "collaborative research", 
        "standards compliance", "ethics in research"
    ],

    "bfsi_investments_trading": [
        "financial modeling", "valuation", "equity research", "fixed income analysis", 
        "derivatives trading", "options strategies", "futures trading", "portfolio management", 
        "wealth management", "risk management", "basel iii", "credit analysis", 
        "fundamental analysis", "technical analysis", "bloomberg terminal", "thomson reuters eikon", 
        "quantitative finance", "python for finance", "r for finance", "algorithmic trading", 
        "backtesting strategies", "asset allocation", "mutual funds", "etfs", 
        "hedge funds", "private equity", "venture capital", "investment banking", 
        "mergers and acquisitions", "ipo process", "regulatory compliance", "sebi guidelines", 
        "fintech", "blockchain in finance", "cryptocurrency trading"
    ],

    "administration_facilities": [
        "office management", "facility management", "vendor management", "contract management", 
        "budgeting", "inventory management", "procurement", "logistics coordination", 
        "maintenance scheduling", "space planning", "event management", "travel management", 
        "calendar management", "meeting coordination", "document management", 
        "health and safety compliance", "fire safety", "emergency preparedness", 
        "front office operations", "mailroom management", "asset tracking", 
        "erp systems", "sap", "oracle erp", "microsoft dynamics", "facility audits", 
        "cost optimization", "stakeholder communication"
    ],

    "quality_assurance": [
        "quality control", "qa methodologies", "iso 9001", "six sigma", "lean qa", 
        "test planning", "test cases", "test execution", "defect tracking", 
        "automation testing", "selenium", "cypress", "playwright", "appium", 
        "performance testing", "jmeter", "loadrunner", "security testing", 
        "penetration testing", "unit testing", "integration testing", 
        "regression testing", "acceptance testing", "uats", "qa dashboards", 
        "jira", "bugzilla", "testlink", "quality metrics", "compliance audits", 
        "continuous testing", "shift-left testing"
    ],

    "media_production_entertainment": [
        "video production", "film editing", "premiere pro", "final cut pro", "after effects", 
        "audition", "sound editing", "color grading", "cinematography", "lighting design", 
        "set design", "scriptwriting", "storyboarding", "animation", "blender", 
        "maya", "3ds max", "motion graphics", "broadcasting", "live streaming", 
        "social media content", "youtube production", "podcasting", "audio mixing", 
        "voiceover recording", "photography", "adobe photoshop", "adobe illustrator", 
        "visual effects (vfx)", "cgi", "production management"
    ],

    "strategic_top_management": [
        "business strategy", "corporate governance", "organizational leadership", 
        "vision and mission planning", "kpi design", "okrs", "strategic planning", 
        "mergers and acquisitions", "corporate restructuring", "change management", 
        "stakeholder management", "board reporting", "financial oversight", 
        "risk assessment", "policy making", "market expansion", "competitive strategy", 
        "global operations management", "digital transformation", "innovation strategy", 
        "public relations", "investor relations", "succession planning", 
        "cross-cultural leadership", "csr strategy", "business ethics"
    ],

    "procurement_supply_chain": [
        "supply chain management", "procurement", "strategic sourcing", "vendor management", 
        "contract negotiation", "inventory control", "warehouse management", "logistics", 
        "transportation management", "distribution management", "demand forecasting", 
        "material requirements planning", "erp systems", "sap mm", "oracle scm", 
        "just in time (jit)", "lean supply chain", "cost optimization", "supplier evaluation", 
        "global sourcing", "import/export compliance", "trade regulations", 
        "reverse logistics", "cold chain management", "last-mile delivery", 
        "supply chain analytics", "blockchain in supply chain"
    ],

    "legal_regulatory": [
        "corporate law", "contract law", "intellectual property rights", "patent filing", 
        "trademark registration", "employment law", "labor compliance", 
        "litigation management", "arbitration", "legal research", 
        "drafting agreements", "memorandum of understanding (mou)", "ndas", 
        "regulatory compliance", "company secretarial work", "roc filings", 
        "sebi compliance", "gdpr compliance", "hipaa compliance", 
        "due diligence", "legal risk assessment", "policy drafting", 
        "corporate governance", "case management systems", "lexisnexis", 
        "westlaw", "legal advisory", "mergers and acquisitions (m&a)"
    ],

    "risk_management_compliance": [
        "enterprise risk management", "operational risk", "financial risk", 
        "market risk", "credit risk", "it risk management", "business continuity planning", 
        "disaster recovery planning", "internal audit", "regulatory compliance", 
        "sox compliance", "basel norms", "aml compliance", "kyc", 
        "fraud detection", "compliance monitoring", "policy enforcement", 
        "risk control matrix", "iso 31000", "risk registers", "incident management", 
        "risk analytics", "reporting dashboards", "third-party risk", 
        "governance risk compliance (grc)", "ethics compliance", "whistleblower policy"
    ],

    "merchandising_retail_ecommerce": [
        "merchandising", "planogram design", "retail analytics", "store operations", 
        "inventory planning", "product assortment", "category management", 
        "pricing strategy", "point of sale (pos) systems", "customer relationship management", 
        "shopify", "woocommerce", "magento", "bigcommerce", "amazon seller central", 
        "ebay seller hub", "flipkart seller hub", "supply chain coordination", 
        "omnichannel retail", "digital marketing", "seo", "sem", 
        "email marketing", "social commerce", "influencer marketing", 
        "visual merchandising", "retail promotions", "payment gateways", 
        "upi integrations", "cashless transactions"
    ],

    "food_beverage_hospitality": [
        "hotel management", "restaurant operations", "food production", 
        "kitchen management", "menu planning", "beverage management", 
        "bar management", "housekeeping", "front office operations", 
        "reservation systems", "pms (opera, fidelio)", "guest relations", 
        "event management", "banquet operations", "catering", 
        "fssai compliance", "food safety standards", "haccp", "quality control", 
        "cost control", "vendor coordination", "hospitality marketing", 
        "travel desk management", "customer experience", 
        "luxury hospitality management", "airline catering"
    ],

    "environment_health_safety": [
        "ehs compliance", "osha standards", "iso 14001", "iso 45001", 
        "workplace safety", "environmental audits", "hazard management", 
        "incident investigation", "root cause analysis", "safety training", 
        "ppe management", "fire safety", "emergency preparedness", 
        "waste management", "hazardous material handling", "risk assessment", 
        "sustainability practices", "carbon footprint analysis", 
        "water conservation", "renewable energy compliance", 
        "green building standards", "ehs reporting", "occupational health"
    ],

    "energy_mining": [
        "renewable energy", "solar energy", "wind energy", "hydropower", 
        "geothermal energy", "oil & gas exploration", "drilling operations", 
        "mining operations", "mineral processing", "metallurgy", 
        "power generation", "thermal power", "nuclear power", 
        "energy trading", "pipeline management", "reservoir engineering", 
        "environmental impact assessment", "ehs compliance", "mine safety", 
        "sustainable mining", "smart grids", "energy auditing", 
        "scada systems", "power distribution", "transmission systems"
    ],

    "sports_fitness_personal_care": [
        "fitness training", "personal training", "yoga instruction", 
        "pilates", "aerobics", "strength training", "cardio training", 
        "sports coaching", "athletic training", "physiotherapy", 
        "sports nutrition", "diet planning", "zumba", "kickboxing", 
        "martial arts", "swimming coaching", "football coaching", 
        "cricket coaching", "gym management", "fitness equipment handling", 
        "injury prevention", "wellness programs", "mental wellness coaching", 
        "spa management", "salon management", "beauty therapy", 
        "skin care", "hair care", "cosmetology"
    ],

    "csr_social_service": [
        "corporate social responsibility", "ngo management", 
        "community development", "women empowerment", 
        "child welfare", "rural development", "education programs", 
        "skill development initiatives", "public health initiatives", 
        "fundraising", "donor management", "grant writing", 
        "volunteer management", "stakeholder engagement", 
        "csr compliance", "impact assessment", "sustainability reporting", 
        "environmental conservation", "social entrepreneurship", 
        "poverty alleviation", "microfinance initiatives", 
        "disaster relief management", "partnership building"
    ],

    "shipping_maritime": [
        "logistics management", "shipping operations", "freight forwarding", 
        "customs clearance", "port operations", "cargo handling", 
        "vessel operations", "chartering", "maritime law", 
        "international trade compliance", "incoterms", "bill of lading", 
        "container management", "supply chain logistics", "import/export operations", 
        "warehouse management", "inventory control", "hazardous cargo handling", 
        "marine engineering", "navigation systems", "marine safety", 
        "ship maintenance", "fleet management"
    ],

    "security_services": [
        "physical security", "surveillance systems", "cctv monitoring", 
        "access control", "biometric systems", "alarm systems", 
        "fire safety systems", "cybersecurity basics", "threat assessment", 
        "security audits", "loss prevention", "event security", 
        "vip protection", "investigations", "crowd management", 
        "patrolling", "emergency response", "disaster management", 
        "conflict resolution", "first aid training", "guard management", 
        "incident reporting", "crisis management"
    ]
}

# Job Profiles Database
JOB_PROFILES = {
    "Engineering - Software & QA": [
        "Software Developer", "Frontend Developer", "Backend Developer", "Full Stack Developer", 
        "Mobile App Developer", "QA Tester", "Automation Engineer", "DevOps Engineer", 
        "Cloud Engineer", "Data Engineer", "BI Engineer", "Machine Learning Engineer", 
        "Site Reliability Engineer"
    ],
    "Human Resources": [
        "Recruiter", "Talent Acquisition Specialist", "HR Business Partner", 
        "Compensation & Benefits Specialist", "Payroll Analyst", "Learning & Development Specialist", 
        "Employee Engagement Specialist", "HR Generalist", "HRIS Analyst", "Employee Relations Specialist", 
        "Organizational Development Specialist", "Diversity & Inclusion Specialist"
    ],
    "Finance & Accounting": [
        "Tax Analyst", "Payroll Accountant", "Forensic Accountant", "Investment Analyst", 
        "Equity Research Associate", "Treasury Analyst", "Cost Accountant", "Financial Risk Analyst",
        "Financial Analyst", "Tax Consultant", "Auditor", "Chartered Accountant", "Investment Banker",
        "Fund Accountant", "Accounts Payable Specialist"
    ],
    "Sales & Business Development": [
        "Sales Development Representative", "Account Executive", "Business Development Executive", 
        "Channel Sales Specialist", "Enterprise Account Executive", "Inside Sales Specialist", 
        "Territory Sales Representative", "Pre-Sales Consultant", "Solutions Consultant"
    ],
    "Marketing & Communications": [
        "Digital Marketing Specialist", "SEO Specialist", "Content Writer", "Content Strategist", 
        "Social Media Manager", "Brand Manager", "Performance Marketing Analyst", 
        "Marketing Automation Specialist", "Public Relations Specialist", "Communications Specialist"
    ],
    "Customer Support & Success": [
        "Customer Support Specialist", "Technical Support Engineer", "Customer Success Manager", 
        "Onboarding Specialist", "Implementation Specialist", "Helpdesk Analyst", 
        "Product Support Engineer", "Escalation Engineer"
    ],
    "Product Management": [
        "Product Analyst", "Associate Product Manager", "Technical Product Manager", "Product Owner", 
        "Growth Product Manager", "Platform Product Manager", "Data Product Manager", "Innovation Manager",
        "AI Product Manager", "E-commerce Product Manager", "API Product Manager", "Mobile Product Manager", 
        "Hardware Product Manager"
    ],
    "Design & User Experience": [
        "UX Designer", "UI Designer", "Interaction Designer", "UX Researcher", "Visual Designer", 
        "Product Designer", "Motion Designer", "Service Designer", "Accessibility Specialist",
        "Information Architect", "Game Designer", "Design Researcher", "3D Designer"
    ],
    "Consulting": [
        "Management Consultant", "Strategy Consultant", "IT Consultant", "Operations Consultant", 
        "Sustainability Consultant", "Financial Consultant", "Business Process Consultant", 
        "Healthcare Consultant", "Risk Consultant"
    ],
    "IT & Information Security": [
        "IT Support Engineer", "Network Administrator", "Systems Engineer", "Cloud Security Specialist", 
        "Information Security Analyst", "Penetration Tester", "SOC Analyst", "Incident Response Specialist", 
        "Identity & Access Management Specialist", "Forensics Analyst"
    ],
    "Data Science & Analytics": [
        "Data Scientist", "Data Analyst", "Machine Learning Engineer", "Data Engineer", 
        "Business Intelligence Analyst", "Quantitative Analyst", "AI Researcher", "Decision Scientist", 
        "Computer Vision Engineer", "Natural Language Processing Engineer"
    ],
    "Content, Editorial & Journalism": [
        "Content Writer", "Copywriter", "Technical Writer", "Journalist", "Editor", "Proofreader", 
        "Content Strategist", "Investigative Reporter", "Broadcast Journalist", "Photojournalist"
    ],
    "Teaching & Training": [
        "School Teacher", "College Professor", "Corporate Trainer", "Instructional Designer", 
        "Curriculum Developer", "E-learning Specialist", "Education Consultant", "Special Education Teacher", 
        "Language Instructor", "Lab Instructor"
    ],
    "Project & Program Management": [
        "Project Coordinator", "Program Analyst", "Scrum Master", "Agile Coach", "Portfolio Manager", 
        "PMO Analyst", "Implementation Manager", "Delivery Manager", "Risk Manager", "Project Scheduler"
    ],
    "Healthcare & Life Sciences": [
        "Medical Doctor", "Nurse", "Pharmacist", "Lab Technician", "Clinical Research Associate", 
        "Biomedical Engineer", "Public Health Specialist", "Genetic Counselor", "Healthcare Data Analyst", 
        "Radiologist"
    ],
    "Engineering - Hardware & Networks": [
        "Network Engineer", "Hardware Engineer", "Embedded Systems Engineer", "FPGA Developer", 
        "VLSI Engineer", "Systems Administrator", "Wireless Network Engineer", "IoT Hardware Engineer", 
        "Chip Design Engineer", "Telecommunications Engineer"
    ],
    "Construction & Site Engineering": [
        "Civil Engineer", "Site Engineer", "Structural Engineer", "Quantity Surveyor", 
        "Construction Project Engineer", "Geotechnical Engineer", "Safety Engineer", "MEP Engineer", 
        "Highway Engineer", "Urban Planner"
    ],
    "Production, Manufacturing & Engineering": [
        "Production Engineer", "Manufacturing Engineer", "Process Engineer", "Industrial Engineer", 
        "Tooling Engineer", "Automation Engineer", "Quality Control Engineer", "Maintenance Engineer", 
        "Lean Manufacturing Specialist", "Plant Engineer"
    ],
    "Research & Development": [
        "R&D Engineer", "Research Scientist", "Innovation Specialist", "Lab Researcher", 
        "Clinical Research Scientist", "AI Researcher", "Product Innovation Engineer", "Material Scientist", 
        "Pharmaceutical Researcher", "Biotechnology Researcher"
    ],
    "BFSI, Investments & Trading": [
        "Equity Research Analyst", "Portfolio Manager", "Risk Analyst", "Derivatives Trader", 
        "Credit Analyst", "Wealth Manager", "Fixed Income Analyst", "Investment Strategist", 
        "Commodities Trader", "Actuary"
    ],
    "Administration & Facilities": [
        "Office Administrator", "Facilities Coordinator", "Front Desk Executive", "Travel Coordinator", 
        "Executive Assistant", "Office Manager", "Records Clerk", "Property Administrator", 
        "Workplace Services Specialist", "Receptionist"
    ],
    "Quality Assurance": [
        "QA Engineer", "Test Automation Engineer", "Performance Tester", "Manual Tester", 
        "Validation Engineer", "Compliance Tester", "Security Tester", "Mobile App Tester", 
        "Game Tester", "Quality Control Analyst"
    ],
    "Media Production & Entertainment": [
        "Video Editor", "Film Director", "Scriptwriter", "Cinematographer", "Sound Engineer", 
        "Broadcast Producer", "Animator", "VFX Artist", "Music Producer", "Radio Jockey"
    ],
    "Strategic & Top Management": [
        "Strategy Analyst", "Corporate Strategist", "Business Transformation Lead", "Chief Strategy Officer", 
        "Mergers & Acquisitions Specialist", "Organizational Development Specialist", "Innovation Manager", 
        "Business Continuity Planner", "Growth Strategist", "Management Consultant"
    ],
    "Procurement & Supply Chain": [
        "Supply Chain Analyst", "Logistics Coordinator", "Procurement Specialist", "Inventory Planner", 
        "Warehouse Operations Supervisor", "Sourcing Specialist", "Demand Planner", "Freight Forwarding Executive", 
        "Import/Export Specialist", "Category Manager"
    ],
    "Legal & Regulatory": [
        "Corporate Lawyer", "Legal Counsel", "Regulatory Affairs Specialist", "Compliance Officer", 
        "Contract Manager", "Paralegal", "Intellectual Property Lawyer", "Litigation Associate", 
        "Data Privacy Officer", "Environmental Law Specialist"
    ],
    "Risk Management & Compliance": [
        "Risk Analyst", "Fraud Investigator", "Internal Auditor", "Operational Risk Specialist", 
        "Market Risk Analyst", "Credit Risk Officer", "Enterprise Risk Manager", "Regulatory Compliance Analyst", 
        "AML Specialist", "Cyber Risk Consultant"
    ],
    "Merchandising, Retail & eCommerce": [
        "Merchandiser", "Store Planner", "Retail Buyer", "Category Planner", "eCommerce Specialist", 
        "Online Marketplace Manager", "Visual Merchandiser", "Inventory Analyst", "Omnichannel Specialist", 
        "Point of Sale (POS) Analyst"
    ],
    "Food, Beverage & Hospitality": [
        "Chef", "Sous Chef", "Pastry Chef", "Restaurant Manager", "Food & Beverage Manager", 
        "Hotel Front Office Executive", "Housekeeping Supervisor", "Event Coordinator", "Sommelier", 
        "Catering Manager"
    ],
    "Environment Health & Safety": [
        "Environmental Engineer", "Health & Safety Officer", "Sustainability Specialist", "EHS Auditor", 
        "Industrial Hygienist", "Safety Inspector", "Environmental Compliance Specialist", 
        "Occupational Health Specialist", "Waste Management Engineer", "Fire Safety Officer"
    ],
    "Energy & Mining": [
        "Petroleum Engineer", "Mining Engineer", "Geologist", "Energy Analyst", "Drilling Engineer", 
        "Renewable Energy Specialist", "Reservoir Engineer", "Pipeline Engineer", "Power Plant Operator", 
        "Solar/Wind Energy Engineer"
    ],
    "Sports, Fitness & Personal Care": [
        "Fitness Trainer", "Sports Coach", "Physiotherapist", "Athletic Trainer", "Yoga Instructor", 
        "Dietitian", "Rehabilitation Specialist", "Personal Trainer", "Sports Scientist", "Wellness Consultant"
    ],
    "CSR & Social Service": [
        "CSR Coordinator", "Community Outreach Specialist", "Social Worker", "NGO Program Officer", 
        "Fundraising Specialist", "Grant Writer", "Volunteer Coordinator", "Development Associate", 
        "Humanitarian Aid Worker", "Advocacy Officer"
    ],
    "Shipping & Maritime": [
        "Marine Engineer", "Ship Captain", "Deck Officer", "Navigation Officer", "Port Operations Manager", 
        "Marine Surveyor", "Naval Architect", "Logistics Officer (Maritime)", "Radio Officer", 
        "Ship Superintendent"
    ],
    "Security Services": [
        "Security Guard", "Surveillance Operator", "Loss Prevention Specialist", "Close Protection Officer", 
        "Cybersecurity Guard", "Patrol Officer", "Event Security Specialist", "Security Systems Operator", 
        "Emergency Response Officer", "Access Control Specialist"
    ]
}

# Certifications Database
CERTIFICATIONS = {
    "cloud_certifications": [
        "AWS Certified Solutions Architect – Associate", "AWS Certified Solutions Architect – Professional", 
        "AWS Certified Developer – Associate", "AWS Certified DevOps Engineer – Professional", 
        "Microsoft Certified: Azure Fundamentals (AZ-900)", "Microsoft Certified: Azure Administrator Associate (AZ-104)", 
        "Microsoft Certified: Azure Solutions Architect Expert (AZ-305)", "Google Associate Cloud Engineer", 
        "Google Professional Cloud Architect", "Google Professional Data Engineer", 
        "Oracle Cloud Infrastructure Architect Associate", "IBM Cloud Professional Architect", 
        "Alibaba Cloud Certified Associate"
    ],
    "data_certifications": [
        "Microsoft Certified: Power BI Data Analyst Associate (PL-300)", "Microsoft Certified: Azure Data Fundamentals (DP-900)", 
        "Microsoft Certified: Azure Database Administrator Associate (DP-300)", "Google Data Analytics Professional Certificate", 
        "Google Advanced Data Analytics Professional Certificate", "Tableau Desktop Specialist", 
        "Tableau Certified Data Analyst", "SAS Certified Specialist: Base Programming", 
        "Cloudera Certified Data Analyst", "Databricks Certified Data Engineer Associate", 
        "Databricks Certified Machine Learning Professional", "Snowflake SnowPro Core Certification", 
        "MongoDB Certified Developer Associate"
    ],
    "cybersecurity_certifications": [
        "CompTIA Security+", "CompTIA CySA+", "CompTIA Pentest+", "Certified Ethical Hacker (CEH)", 
        "Certified Information Systems Security Professional (CISSP)", "Certified Information Security Manager (CISM)", 
        "Certified Cloud Security Professional (CCSP)", "Offensive Security Certified Professional (OSCP)", 
        "GIAC Security Essentials (GSEC)", "GIAC Penetration Tester (GPEN)", "Cisco Certified CyberOps Associate"
    ],
    "networking_certifications": [
        "CompTIA Network+", "Cisco Certified Network Associate (CCNA)", "Cisco Certified Network Professional (CCNP)", 
        "Cisco Certified Internetwork Expert (CCIE)", "Juniper Networks Certified Associate (JNCIA)", 
        "Aruba Certified Mobility Associate (ACMA)"
    ],
    "devops_certifications": [
        "Docker Certified Associate", "Certified Kubernetes Administrator (CKA)", "Certified Kubernetes Application Developer (CKAD)", 
        "HashiCorp Certified: Terraform Associate", "Red Hat Certified Specialist in OpenShift Administration", 
        "Microsoft Certified: DevOps Engineer Expert (AZ-400)", "AWS Certified DevOps Engineer – Professional", 
        "GitLab Certified Associate"
    ],
    "software_engineering_certifications": [
        "Oracle Certified Professional: Java SE", "Microsoft Certified: C# Developer", 
        "PCEP – Certified Entry-Level Python Programmer", "PCAP – Certified Associate in Python Programming", 
        "Google Associate Android Developer", "AWS Certified Developer – Associate", 
        "Scrum.org Professional Scrum Developer"
    ],
    "project_management_certifications": [
        "Project Management Professional (PMP)", "Certified Associate in Project Management (CAPM)", 
        "PRINCE2 Foundation", "PRINCE2 Practitioner", "Agile Certified Practitioner (PMI-ACP)", 
        "Certified ScrumMaster (CSM)", "SAFe Agilist Certification", "Lean Six Sigma Green Belt", 
        "Lean Six Sigma Black Belt"
    ],
    "ai_ml_certifications": [
        "AWS Certified Machine Learning – Specialty", "Microsoft Certified: Azure AI Engineer Associate", 
        "Google TensorFlow Developer Certificate", "IBM AI Engineering Professional Certificate", 
        "DeepLearning.AI Machine Learning Specialization", "Stanford Online Machine Learning Certificate (Coursera)"
    ],
    "database_certifications": [
        "Oracle Database SQL Certified Associate", "Oracle Certified Professional: MySQL Database Administrator", 
        "Microsoft Certified: SQL Server Database Development", "MongoDB Certified DBA", 
        "PostgreSQL Certified Professional", "Cassandra Developer Certification"
    ],
    "it_service_management_certifications": [
        "ITIL 4 Foundation", "ITIL 4 Managing Professional", "COBIT 2019 Foundation", "ISO/IEC 20000 Foundation"
    ]
}

def get_all_skills() -> Dict[str, str]:
    """
    Get a flattened dictionary of all skills with their normalized names.
    Returns a mapping of skill variants to normalized skill names.
    """
    skills_mapping = {}
    
    # Combine all skill categories
    all_skills = {**COMPREHENSIVE_SKILLS, **ADDITIONAL_SKILLS}
    
    for category, skills in all_skills.items():
        for skill in skills:
            # Create multiple variants for each skill
            skill_lower = skill.lower()
            skills_mapping[skill_lower] = skill.title()
            
            # Add common variants
            if " " in skill_lower:
                # Add version without spaces
                no_space = skill_lower.replace(" ", "")
                skills_mapping[no_space] = skill.title()
                
                # Add version with hyphens
                hyphenated = skill_lower.replace(" ", "-")
                skills_mapping[hyphenated] = skill.title()
                
                # Add version with underscores
                underscored = skill_lower.replace(" ", "_")
                skills_mapping[underscored] = skill.title()
    
    return skills_mapping

def get_skills_by_category(category: str) -> List[str]:
    """Get skills for a specific category."""
    all_skills = {**COMPREHENSIVE_SKILLS, **ADDITIONAL_SKILLS}
    return all_skills.get(category, [])

def get_all_job_profiles() -> Dict[str, List[str]]:
    """Get all job profiles organized by category."""
    return JOB_PROFILES

def get_all_certifications() -> Dict[str, List[str]]:
    """Get all certifications organized by category."""
    return CERTIFICATIONS

def search_skills(query: str) -> List[str]:
    """
    Search for skills that match the given query.
    Returns a list of matching skills.
    """
    query_lower = query.lower()
    matching_skills = []
    
    all_skills = {**COMPREHENSIVE_SKILLS, **ADDITIONAL_SKILLS}
    
    for category, skills in all_skills.items():
        for skill in skills:
            if query_lower in skill.lower():
                matching_skills.append(skill)
    
    return list(set(matching_skills))  # Remove duplicates
