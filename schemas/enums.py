from __future__ import annotations

from enum import Enum
from functools import lru_cache


class UnifiedJobLevelCategory(str, Enum):
    """Unified job level categorization combining holding and techpack approaches."""
    EXECUTIVE_MANAGEMENT = "Захирал"  # CEO, Deputy Directors
    SENIOR_MANAGEMENT = "Дарга/Нэгжийн удирдлага"  # Directors, Senior Managers
    MIDDLE_MANAGEMENT = "Ахлах менежер"  # Senior Managers, Department Heads
    MANAGER = "Менежер"  # Managers, Team Leads
    SPECIALIST_SENIOR = "Ахлах мэргэжилтэн"  # Senior Specialists
    SPECIALIST = "Мэргэжилтэн"  # Specialists
    STAFF = "Ажилтан"  # General Staff

    @classmethod
    @lru_cache(maxsize=1)
    def _descriptions(cls) -> dict[UnifiedJobLevelCategory, str]:
        return {
            cls.EXECUTIVE_MANAGEMENT:
                "Top executive leadership (CEO, Deputy Directors, C-suite). Job grades 10-11. "
                "Responsible for overall organizational strategy, board-level decisions, and company-wide management. "
                "Requires 15+ years experience with proven executive track record.",
            cls.SENIOR_MANAGEMENT:
                "Senior leadership roles (Directors, Functional Heads). Job grades 8-9. "
                "Manages multiple departments or major functions, sets strategic direction within domain, "
                "develops senior managers. Requires 10-15 years experience.",
            cls.MIDDLE_MANAGEMENT:
                "Senior management (Senior Managers, Department Heads). Job grades 7-8. "
                "Manages multiple teams/departments, tactical execution, budget oversight. "
                "Requires 7-12 years experience with leadership capabilities.",
            cls.MANAGER:
                "Mid-level management (Managers, Team Leads, Supervisors). Job grades 6-7. "
                "Manages teams, day-to-day execution, people management. "
                "Requires 4-8 years experience with leadership capabilities.",
            cls.SPECIALIST_SENIOR:
                "Senior professional specialists with advanced expertise. Job grades 5-6. "
                "Subject matter experts, complex problem solving, mentoring, project leadership. "
                "Requires 6-10 years specialized experience.",
            cls.SPECIALIST:
                "Professional specialists with domain expertise. Job grades 3-4. "
                "Independent professional work, specialized skills, moderate complexity tasks. "
                "Requires 2-6 years experience with university degree.",
            cls.STAFF:
                "Entry to junior level staff positions. Job grades 1-2. "
                "Operational tasks, foundational work, learning and executing procedures. "
                "Requires 0-3 years experience.",
        }

    @property
    def description(self) -> str:
        return self._descriptions().get(self, self.value)

    @classmethod
    @lru_cache(maxsize=1)
    def _multipliers(cls) -> dict[UnifiedJobLevelCategory, float]:
        return {
            cls.EXECUTIVE_MANAGEMENT: 3.5,
            cls.SENIOR_MANAGEMENT: 2.5,
            cls.MIDDLE_MANAGEMENT: 2.0,
            cls.MANAGER: 1.8,
            cls.SPECIALIST_SENIOR: 1.5,
            cls.SPECIALIST: 1.0,
            cls.STAFF: 0.6,
        }

    @property
    def salary_multiplier(self) -> float:
        """Salary multiplier relative to base specialist level."""
        return self._multipliers().get(self, 1.0)


class ExperienceLevel(str, Enum):
    """Experience level categories. as 0-36month, 37-84month, 85+ month"""
    ENTRY = "0-36"
    INTERMEDIATE = "37-84"
    EXPERT = "85+"

    @classmethod
    @lru_cache(maxsize=1)
    def _ranges(cls) -> dict[ExperienceLevel, tuple[int, int]]:
        return {cls.ENTRY: (0, 36), cls.INTERMEDIATE: (37, 84), cls.EXPERT: (85, 1000)}

    @classmethod
    @lru_cache(maxsize=1)
    def _multipliers(cls) -> dict[ExperienceLevel, float]:
        return {cls.ENTRY: 0.7, cls.INTERMEDIATE: 1.0, cls.EXPERT: 1.6}

    @property
    def years_range(self) -> tuple[int, int]:
        return self._ranges().get(self, (0, 2))

    @property
    def salary_multiplier(self) -> float:
        return self._multipliers().get(self, 1.0)


class EducationLevel(str, Enum):
    """Education level categories."""
    HIGH_SCHOOL = "Бүрэн дунд"
    VOCATIONAL = "Мэргэжлийн"
    BACHELOR = "Бакалавр"
    MASTER = "Магистр"
    DOCTORATE = "Доктор"

    @classmethod
    @lru_cache(maxsize=1)
    def _multipliers(cls) -> dict[EducationLevel, float]:
        return {cls.HIGH_SCHOOL: 0.8, cls.VOCATIONAL: 0.9, cls.BACHELOR: 1.0, cls.MASTER: 1.2, cls.DOCTORATE: 1.4}

    @property
    def salary_multiplier(self) -> float:
        return self._multipliers().get(self, 1.0)


class JobFunctionCategory(str, Enum):
    STORAGE = "Агуулах"
    AUDIT_RISK_COMPLIANCE = "Аудит, эрсдэлийн удирдлага, МАБ"
    SALES = "Борлуулалт"
    BUSINESS_DEVELOPMENT = "Бизнес хөгжил"
    EXECUTIVE_MANAGEMENT = "Гүйцэтгэх удирдлага, ТУЗ"
    ADMINISTRATION = "Захиргаа"
    ENGINEERING_TECHNICAL = "Инженеринг, техник, тоног төхөөрөмж"
    CONTENT_DESIGN = "Контент, дизайн"
    MARKETING_PR = "Маркетинг, PR"
    IT_TELECOM = "Мэдээллийн технологи, харилцаа холбоо"
    FINANCE_ACCOUNTING = "Санхүү, НББ, хөрөнгө оруулалт"
    PROJECT_ALL = "Төсөл/бүх төрлийн"
    DISTRIBUTION_TRANSPORT = "Түгээлт, тээвэр"
    MANUFACTURING = "Үйлдвэрлэл"
    SERVICE_CLEANING = "Үйлчилгээ/цэвэрлэгээ"
    HSE_BO = "ХАБЭА,БО"
    CUSTOMER_SERVICE = "Харилцагчийн үйлчилгээ"
    SECURITY = "Харуул хамгаалалт"
    PROCUREMENT = "Худалдан авалт"
    HR = "Хүний нөөц"
    LEGAL = "Эрхзүй хууль"
    HEALTHCARE = "Эрүүл мэнд/эмнэлэг"
    OTHER = "Бусад"

    @classmethod
    @lru_cache(maxsize=1)
    def _descriptions(cls) -> dict[JobFunctionCategory, str]:
        return {
            cls.STORAGE: "Warehouse and storage operations including inventory management, logistics coordination, and materials handling.",
            cls.AUDIT_RISK_COMPLIANCE: "Internal and external audit functions, enterprise risk management, and regulatory compliance activities.",
            cls.SALES: "Direct sales roles focused on revenue generation, client acquisition, and account management across various industries.",
            cls.BUSINESS_DEVELOPMENT: "Strategic growth initiatives including partnership development, market expansion, and new business opportunities.",
            cls.EXECUTIVE_MANAGEMENT: "C-suite and senior leadership positions responsible for overall organizational strategy and direction.",
            cls.ADMINISTRATION: "Administrative support and office management functions ensuring smooth operational workflows.",
            cls.ENGINEERING_TECHNICAL: "Technical and engineering roles involving design, maintenance, and operation of equipment and systems.",
            cls.CONTENT_DESIGN: "Creative roles in content creation, graphic design, multimedia production, and visual communications.",
            cls.MARKETING_PR: "Marketing strategy, brand management, public relations, and communications activities.",
            cls.IT_TELECOM: "Information technology and telecommunications roles including software development, infrastructure, and systems administration.",
            cls.FINANCE_ACCOUNTING: "Financial planning, accounting, investment management, and related financial services.",
            cls.PROJECT_ALL: "Project management and coordination roles across all industries and project types.",
            cls.DISTRIBUTION_TRANSPORT: "Transportation, logistics, and distribution activities for goods and materials.",
            cls.MANUFACTURING: "Production and manufacturing operations including assembly, quality control, and process management.",
            cls.SERVICE_CLEANING: "Service industry roles including cleaning, maintenance, and facility management.",
            cls.HSE_BO: "Health, safety, environment, and business operations management ensuring workplace safety and regulatory compliance.",
            cls.CUSTOMER_SERVICE: "Customer-facing support roles focused on client satisfaction and issue resolution.",
            cls.SECURITY: "Security and protection services including physical security, surveillance, and risk mitigation.",
            cls.PROCUREMENT: "Purchasing, vendor management, and supply chain procurement activities.",
            cls.HR: "Human resources functions including recruitment, employee relations, compensation, and organizational development.",
            cls.LEGAL: "Legal counsel, contract management, and regulatory compliance activities.",
            cls.HEALTHCARE: "Healthcare and medical services including clinical, administrative, and support roles.",
            cls.OTHER: "Roles that do not fit into the predefined categories, encompassing a wide range of job functions across various industries.",
        }

    @property
    def description(self) -> str:
        return self._descriptions().get(self, self.value)


class JobIndustryCategory(str, Enum):
    AGRICULTURE_FORESTRY_FISHING_HUNTING = "Хөдөө_аж_ахуй_ойн_аж_ахуй_загас_барилт_ан_агнуур"
    MINING_QUARRYING_OIL_GAS_EXTRACTION = "Уул_уурхай_олборлолт"
    MANUFACTURING = "Боловсруулах_үйлдвэрлэл"
    ELECTRICITY_GAS_STEAM_AIR_CONDITIONING_SUPPLY = "Цахилгаан_хий_уур_агааржуулалт"
    WATER_SEWERAGE_WASTE_MANAGEMENT_REMEDIATION = "Ус_хангамж_сувагжилтын_систем_хог_хаягдал_зайлуулах_болон_хүрээлэн_буй_орчныг_дахин_сэргээх_үйл_ажиллагаа"
    CONSTRUCTION = "Барилга"
    WHOLESALE_RETAIL_TRADE_REPAIR_MOTOR_VEHICLES_MOTORCYCLES = "Бөөний_болон_жижиглэн_худалдаа_машин_мотоциклийн_засвар_үйлчилгээ"
    TRANSPORTATION_WAREHOUSING = "Тээвэр_агуулахын_үйл_ажиллагаа"
    ACCOMMODATION_FOOD_SERVICES = "Зочид_буудал_байр_сууц_болон_нийтийн_хоолны_үйлчилгээ"
    INFORMATION_COMMUNICATION = "Мэдээлэл_холбоо"
    FINANCE_INSURANCE = "Санхүүгийн_болон_даатгалын_үйл_ажиллагаа"
    REAL_ESTATE_RENTAL_LEASING = "Үл хөдлөх хөрөнгийн үйл ажиллагаа"
    PROFESSIONAL_SCIENTIFIC_TECHNICAL_SERVICES = "Мэргэжлийн шинжлэх ухаан болон техникийн үйл ажиллагаа"
    MANAGEMENT_SUPPORT_WASTE_MANAGEMENT_REMIDIATION_SERVICES = "Удирдлагын болон дэмжлэг үзүүлэх үйл ажиллагаа"
    PUBLIC_ADMINISTRATION_DEFENSE_SOCIAL_SECURITY = "Төрийн удирдлага, батлан хамгаалах үйл ажиллагаа, албан журмын нийгмийн хамгаалал"
    EDUCATION = "Боловсрол"
    HEALTHCARE_SOCIAL_ASSISTANCE = "Хүний эрүүл мэнд, нийгмийн халамжийн үйл ажиллагаа"
    ARTS_ENTERTAINMENT_RECREATION = "Урлаг, үзвэр, тоглоом, наадам"
    OTHER_SERVICES = "Үйлчилгээний бусад үйл ажиллагаа"
    HOUSEHOLD_EMPLOYERS = "Хүн хөлслөн ажиллуулдаг өрхийн үйл ажиллагаа, өрхийн өөрийн хэрэглээнд зориулан үйлдвэрлэсэн нэр төрлөөр нь тодорхойлох боломжгүй бүтээгдэхүүн үйлчилгээ"
    INTERNATIONAL_ORGANIZATION_DIPLOMATIC_SERVICES = "Олон улсын байгууллага, суурин төлөөлөгчийн үйл ажиллагаа"
    OTHER = "Бусад"

    @classmethod
    @lru_cache(maxsize=1)
    def _descriptions(cls) -> dict[JobIndustryCategory, str]:
        return {
            cls.AGRICULTURE_FORESTRY_FISHING_HUNTING: "Agriculture, forestry, fishing, and hunting industry including crop production, animal production, forestry, fishing, and related activities.",
            cls.MINING_QUARRYING_OIL_GAS_EXTRACTION: "Mining and extraction of minerals, oil, gas, and other natural resources.",
            cls.MANUFACTURING: "Manufacturing of goods across various sectors including food production, textiles, machinery, and more.",
            cls.ELECTRICITY_GAS_STEAM_AIR_CONDITIONING_SUPPLY: "Generation and distribution of electricity, gas, steam, and air conditioning supply.",
            cls.WATER_SEWERAGE_WASTE_MANAGEMENT_REMEDIATION: "Water supply and sewage systems, waste management services, and environmental remediation activities.",
            cls.CONSTRUCTION: "Construction of buildings, infrastructure projects, and related activities.",
            cls.WHOLESALE_RETAIL_TRADE_REPAIR_MOTOR_VEHICLES_MOTORCYCLES: "Wholesale and retail trade of motor vehicles and motorcycles including repair services.",
            cls.TRANSPORTATION_WAREHOUSING: "Transportation of goods and passengers as well as warehousing and storage services.",
            cls.ACCOMMODATION_FOOD_SERVICES: "Accommodation services such as hotels and food services including restaurants and catering.",
            cls.INFORMATION_COMMUNICATION: "Information technology services, telecommunications, and related communication services.",
            cls.FINANCE_INSURANCE: "Financial services including banking, insurance, investment management, and related activities.",
            cls.REAL_ESTATE_RENTAL_LEASING: "Real estate activities including rental and leasing of properties.",
            cls.PROFESSIONAL_SCIENTIFIC_TECHNICAL_SERVICES: "Professional services in scientific research, technical consulting, legal advice, accounting, and similar fields.",
            cls.MANAGEMENT_SUPPORT_WASTE_MANAGEMENT_REMIDIATION_SERVICES: "Management support services including administrative support, waste management services, and remediation services.",
            cls.PUBLIC_ADMINISTRATION_DEFENSE_SOCIAL_SECURITY: "Public administration including government services, defense activities, social security administration.",
            cls.EDUCATION: "Educational services including schools, universities, training centers.",
            cls.HEALTHCARE_SOCIAL_ASSISTANCE: "Healthcare services including hospitals, clinics, social assistance services.",
            cls.ARTS_ENTERTAINMENT_RECREATION: "Arts, entertainment, and recreation services including performing arts, spectator sports, museums, and amusement parks.",
            cls.OTHER_SERVICES: "Other services not classified in the above categories including repair and maintenance services, personal services, and similar activities.",
            cls.HOUSEHOLD_EMPLOYERS: "Household employers including domestic workers, nannies, housekeepers, and similar roles.",
            cls.INTERNATIONAL_ORGANIZATION_DIPLOMATIC_SERVICES: "International organizations and diplomatic services including roles in embassies, consulates, international agencies, and similar entities.",
            cls.OTHER: "Other categories not specifically listed.",
        }

    @property
    def description(self) -> str:
        return self._descriptions().get(self, self.value)


class Category(str, Enum):
    """Industry/sector categories from Paylab salary data."""
    ADMINISTRATION = "Administration"
    AGRICULTURE_FOOD_INDUSTRY = "Agriculture, Food Industry"
    ARTS_CULTURE = "Arts & Culture"
    BANKING = "Banking"
    CAR_INDUSTRY = "Car Industry"
    CHEMICAL_INDUSTRY = "Chemical Industry"
    COMMERCE = "Commerce"
    CONSTRUCTION_REAL_ESTATE = "Construction & Real Estate"
    CUSTOMER_SUPPORT = "Customer Support"
    ECONOMY_FINANCE_ACCOUNTANCY = "Economy, Finance, Accountancy"
    EDUCATION_SCIENCE_RESEARCH = "Education, Science & Research"
    ELECTRICAL_POWER_ENGINEERING = "Electrical & Power Engineering"
    GENERAL_LABOUR = "General labour"
    HUMAN_RESOURCES = "Human Resources"
    INFORMATION_TECHNOLOGY = "Information Technology"
    INSURANCE = "Insurance"
    JOURNALISM_PRINTING_ARTS_MEDIA = "Journalism, Printing Arts & Media"
    LAW_LEGISLATION = "Law & Legislation"
    LEASING = "Leasing"
    MANAGEMENT = "Management"
    MARKETING_ADVERTISING_PR = "Marketing, Advertising, PR"
    MECHANICAL_ENGINEERING = "Mechanical Engineering"
    MEDICINE_SOCIAL_CARE = "Medicine & Social Care"
    MINING_METALLURGY = "Mining, Metallurgy"
    PHARMACEUTICAL_INDUSTRY = "Pharmaceutical Industry"
    PRODUCTION = "Production"
    PUBLIC_ADMINISTRATION_SELF_GOVERNANCE = "Public Administration, Self-governance"
    QUALITY_MANAGEMENT = "Quality Management"
    SECURITY_PROTECTION = "Security & Protection"
    SERVICE_INDUSTRIES = "Service Industries"
    TECHNOLOGY_DEVELOPMENT = "Technology, Development"
    TELECOMMUNICATIONS = "Telecommunications"
    TEXTILE_LEATHER_APPAREL_INDUSTRY = "Textile, Leather, Apparel Industry"
    TOP_MANAGEMENT = "Top Management"
    TOURISM_GASTRONOMY_HOTEL_BUSINESS = "Tourism, Gastronomy, Hotel Business"
    TRANSLATING_INTERPRETING = "Translating, interpreting"
    TRANSPORT_HAULAGE_LOGISTICS = "Transport, Haulage, Logistics"
    WATER_MANAGEMENT_FORESTRY_ENVIRONMENT = "Water Management, Forestry, Environment"
    WOOD_PROCESSING_INDUSTRY = "Wood Processing Industry"

    @classmethod
    @lru_cache(maxsize=1)
    def _mongolian_names(cls) -> dict[Category, str]:
        return {
            cls.ADMINISTRATION: "Захиргаа",
            cls.AGRICULTURE_FOOD_INDUSTRY: "Хөдөө аж ахуй, хүнсний үйлдвэр",
            cls.ARTS_CULTURE: "Урлаг & Соёл",
            cls.BANKING: "Банк",
            cls.CAR_INDUSTRY: "Автомашины үйлдвэр",
            cls.CHEMICAL_INDUSTRY: "Химийн үйлдвэр",
            cls.COMMERCE: "Худалдаа",
            cls.CONSTRUCTION_REAL_ESTATE: "Барилга & Үл хөдлөх хөрөнгө",
            cls.CUSTOMER_SUPPORT: "Үйлчлүүлэгчийн тусламж",
            cls.ECONOMY_FINANCE_ACCOUNTANCY: "Эдийн засаг, Санхүү, Нягтлан бодох бүртгэл",
            cls.EDUCATION_SCIENCE_RESEARCH: "Боловсрол, Шинжлэх ухаан & Судалгаа",
            cls.ELECTRICAL_POWER_ENGINEERING: "Цахилгаан & Эрчим хүчний инженерчлэл",
            cls.GENERAL_LABOUR: "Ерөнхий хөдөлмөр",
            cls.HUMAN_RESOURCES: "Хүний нөөц",
            cls.INFORMATION_TECHNOLOGY: "Мэдээллийн технологи",
            cls.INSURANCE: "Даатгал",
            cls.JOURNALISM_PRINTING_ARTS_MEDIA: "Сэтгүүл зүй, Хэвлэх урлаг & Медиа",
            cls.LAW_LEGISLATION: "Хууль & Хууль тогтоомж",
            cls.LEASING: "Лизинг",
            cls.MANAGEMENT: "Менежмент",
            cls.MARKETING_ADVERTISING_PR: "Маркетинг, Сурталчилгаа, PR",
            cls.MECHANICAL_ENGINEERING: "Механик инженерчлэл",
            cls.MEDICINE_SOCIAL_CARE: "Анагаах ухаан & Нийгмийн халамж",
            cls.MINING_METALLURGY: "Уул уурхай, Металлурги",
            cls.PHARMACEUTICAL_INDUSTRY: "Эмийн үйлдвэр",
            cls.PRODUCTION: "Үйлдвэрлэл",
            cls.PUBLIC_ADMINISTRATION_SELF_GOVERNANCE: "Төрийн захиргаа, Өөрөө удирдах ёс",
            cls.QUALITY_MANAGEMENT: "Чанарын менежмент",
            cls.SECURITY_PROTECTION: "Аюулгүй байдал & Хамгаалалт",
            cls.SERVICE_INDUSTRIES: "Үйлчилгээний салбар",
            cls.TECHNOLOGY_DEVELOPMENT: "Технологи, Хөгжүүлэлт",
            cls.TELECOMMUNICATIONS: "Харилцаа холбоо",
            cls.TEXTILE_LEATHER_APPAREL_INDUSTRY: "Нэхмэл, Арьс шир, Хувцасны үйлдвэр",
            cls.TOP_MANAGEMENT: "Дээд удирдлага",
            cls.TOURISM_GASTRONOMY_HOTEL_BUSINESS: "Аялал жуулчлал, Хоол хүнс, Зочид буудлын бизнес",
            cls.TRANSLATING_INTERPRETING: "Орчуулга, Тайлбарлах",
            cls.TRANSPORT_HAULAGE_LOGISTICS: "Тээвэр, Ачаа тээвэр, Логистик",
            cls.WATER_MANAGEMENT_FORESTRY_ENVIRONMENT: "Усны менежмент, Ойн аж ахуй, Байгаль орчин",
            cls.WOOD_PROCESSING_INDUSTRY: "Модон материал боловсруулах үйлдвэр",
        }

    @property
    def mongolian_name(self) -> str:
        return self._mongolian_names().get(self, self.value)


class PositionalCategory(str, Enum):
    """Positional/job title categories from Paylab salary data."""
    NET_PROGRAMMER = ".NET Programmer"
    ABAP_PROGRAMMER = "ABAP Programmer"
    AI_ENGINEER = "AI Engineer"
    ASP_NET_PROGRAMMER = "ASP.NET Programmer"
    ACCOUNT_DIRECTOR = "Account Director"
    ACCOUNT_EXECUTIVE = "Account Executive"
    ACCOUNT_MANAGER = "Account Manager"
    ACCOUNTANT = "Accountant"
    ACCOUNTING_CLERK = "Accounting Clerk"
    ACCOUNTING_SERVICE_MANAGER = "Accounting service manager"
    ACCOMMODATION_MANAGER = "Accommodation Manager"
    ACTOR = "Actor"
    ACTIVITY_INSTRUCTOR = "Activity Instructor"
    ADMINISTRATIVE_WORKER = "Administrative Worker"
    ADMINISTRATIVE_OFFICER = "Administrative officer"
    AGRICULTURAL_ENGINEER_AGRONOMIST = "Agricultural Engineer, Agronomist"
    AGRICULTURAL_EQUIPMENT_OPERATOR = "Agricultural Equipment Operator"
    AGRICULTURAL_SPECIALIST = "Agricultural Specialist"
    AGRICULTURAL_TECHNICIAN = "Agricultural Technician"
    AGRICULTURAL_TECHNOLOGIST = "Agricultural Technologist"
    AIR_TRAFFIC_CONTROLLER = "Air Traffic Controller"
    AIRCRAFT_TECHNICIAN = "Aircraft Technician"
    AIRCRAFT_ENGINEER = "Aircraft engineer"
    AMBULANCE_DRIVER = "Ambulance Driver"
    AMBULANCE_PARAMEDIC = "Ambulance Paramedic"
    ANESTHETIST = "Anesthetist"
    ANIMAL_CARE_WORKER = "Animal Care Worker"
    ANTI_MONEY_LAUNDERING_SPECIALIST = "Anti-Money Laundering Specialist"
    ARCHAEOLOGIST = "Archaeologist"
    ARCHITECT = "Architect"
    ART_DIRECTOR = "Art Director"
    ARCHIVIST_REGISTRY_ADMINISTRATOR = "Archivist, Registry Administrator"
    ASSISTANT = "Assistant"
    ASSISTANT_COOK = "Assistant Cook"
    ASSISTANT_FINANCIAL_CONTROLLER = "Assistant Financial Controller"
    ASSISTANT_TEACHER = "Assistant Teacher"
    ASSISTANT_OF_AUDITOR = "Assistant of Auditor"
    ASSISTANT_TO_A_TAX_ADVISOR = "Assistant to a Tax Advisor"
    AU_PAIR = "Au-pair"
    AUDITOR = "Auditor"
    AUTO_ELECTRICIAN = "Auto Electrician"
    AUTO_REPAIR_SHOP_MANAGER = "Auto Repair Shop Manager"
    AUTOMATION_ENGINEER = "Automation engineer"
    AUTOMATION_PLANNER = "Automation planner"
    AXEMAN = "Axeman"
    BACK_OFFICE_SPECIALIST = "Back Office Specialist"
    BAILIFF_ENFORCEMENT_OFFICER = "Bailiff/Enforcement Officer"
    BAKER = "Baker"
    BARTENDER = "Bartender"
    BEAUTICIAN = "Beautician"
    BETTING_CLERK = "Betting Clerk"
    BICYCLE_MECHANIC = "Bicycle mechanic"
    BIDDING_ENGINEER = "Bidding engineer"
    BILLING_CLERK = "Billing Clerk"
    BIOLOGIST = "Biologist"
    BOOKBINDER = "Bookbinder"
    BOOKMAKER = "Bookmaker"
    BOOKING_AGENT = "Booking agent"
    BOSUN = "Bosun"
    BRANCH_DIRECTOR = "Branch Director"
    BRAND_MANAGER = "Brand Manager"
    BRICKLAYER = "Bricklayer"
    BUILDING_CONTROL_SURVEYOR = "Building Control Surveyor"
    BUILDING_TECHNICIAN = "Building Technician"
    BUS_DRIVER = "Bus Driver"
    BUSINESS_ANALYST = "Business Analyst"
    BUSINESS_DEVELOPMENT_MANAGER = "Business Development Manager"
    BUSINESS_GROUP_MANAGER = "Business Group Manager"
    BUSINESS_INTELLIGENCE_SPECIALIST = "Business Intelligence Specialist"
    BUTCHER = "Butcher"
    BUYING_AGENT = "Buying Agent"
    C_PROGRAMMER = "C Programmer"
    CSHARP_PROGRAMMER = "C# Programmer"
    CPP_PROGRAMMER = "C++ Programmer"
    CAD_SPECIALIST = "CAD Specialist"
    CNC_MACHINE_SETTER = "CNC Machine Setter"
    CNC_PROGRAMMER = "CNC Programmer"
    CRM_SPECIALIST = "CRM specialist"
    CSR_SPECIALIST = "CSR specialist"
    CABINET_MAKER = "Cabinet Maker"
    CABLE_CAR_OPERATOR = "Cable car operator"
    CALL_CENTER_SUPERVISOR = "Call Center Supervisor"
    CALL_CENTRE_DIRECTOR = "Call Centre Director"
    CALL_CENTRE_MANAGER = "Call Centre Manager"
    CALL_OPERATOR = "Call Operator"
    CAMERA_OPERATOR = "Camera Operator"
    CAR_DRIVER = "Car Driver"
    CAR_FLEET_MANAGER = "Car Fleet Manager"
    CAR_GLASS_FITTER = "Car Glass Fitter"
    CAR_MECHANIC = "Car Mechanic"
    CAR_UPHOLSTERER = "Car Upholsterer"
    CAR_WASH_WORKER = "Car Wash Worker"
    CAR_SALESMAN = "Car salesman"
    CAREER_ADVISOR = "Career advisor"
    CAREGIVER = "Caregiver"
    CARER_PERSONAL_ASSISTANT = "Carer, Personal Assistant"
    CARPENTER = "Carpenter"
    CASEWORKER = "Caseworker"
    CASHIER = "Cashier"
    CATERING_MANAGER = "Catering manager"
    CHAMBERMAID = "Chambermaid"
    CHARGE_NURSE = "Charge Nurse"
    CHEMICAL_ENGINEER = "Chemical Engineer"
    CHEMICAL_LAB_TECHNICIAN = "Chemical Lab Technician"
    CHEMIST = "Chemist"
    CHEF = "Chef"
    CHIEF_ACCOUNTANT = "Chief Accountant"
    CHIEF_ACCOUNTANT_DEPUTY = "Chief Accountant Deputy"
    CHIEF_ADVISOR = "Chief Advisor"
    CHIEF_EXECUTIVE_OFFICER = "Chief Executive Officer"
    CHIEF_OFFICIAL = "Chief Official"
    CHIEF_RECEPTIONIST_OFFICER = "Chief Receptionist Officer"
    CHIEF_STATE_ADVISOR = "Chief State Advisor"
    CHIEF_BOROUGH_CONTROLLER = "Chief borough controller"
    CHOREOGRAPHER = "Choreographer"
    CIVIL_ENGINEER = "Civil Engineer"
    CLAIMS_ADMINISTRATOR = "Claims Administrator"
    CLAIMS_SPECIALIST = "Claims Specialist"
    CLEANER = "Cleaner"
    CLEANING_MANAGER = "Cleaning manager"
    CLIENT_OFFICER = "Client officer"
    CLINICAL_DATA_MANAGER = "Clinical Data Manager"
    CLINICAL_PSYCHOLOGIST = "Clinical Psychologist"
    CLINICAL_RESEARCH_ASSOCIATE = "Clinical Research Associate"
    CLOTHING_TEXTILE_TECHNOLOGIST = "Clothing/textile technologist"
    COACH = "Coach"
    CO_ORDINATOR = "Co-ordinator"
    COBBLER = "Cobbler"
    COLLEGE_LECTOR = "College lector"
    COMPLAINTS_DEPARTMENT_CLERK = "Complaints Department Clerk"
    COMPLIANCE_SPECIALIST = "Compliance Specialist"
    COMPENSATION_BENEFIT_SPECIALIST = "Compensation & Benefit Specialist"
    CONCIERGE = "Concierge"
    CONSTRUCTION_MANAGER = "Construction Manager"
    CONSTRUCTION_PLANT_OPERATOR = "Construction Plant Operator"
    CONSTRUCTION_WORKER = "Construction worker"
    CONSULTANT = "Consultant"
    CONTENT_PROVIDER = "Content provider"
    CONTRACT_ADMINISTRATOR = "Contract administrator"
    CONTROLLER = "Controller"
    COOK = "Cook"
    COPYWRITER = "Copywriter"
    COST_ACCOUNTANT = "Cost Accountant"
    COUNTER_CLERK = "Counter Clerk"
    COUNTRY_MANAGER_DIRECTOR = "Country Manager/Director"
    COURIER = "Courier"
    CRANE_OPERATOR = "Crane Operator"
    CRISIS_WORKER = "Crisis worker"
    CROUPIER = "Croupier"
    CULTURAL_OFFICER = "Cultural Officer"
    CURATOR = "Curator"
    CUSTOMER_RELATIONSHIP_MANAGER = "Customer Relationship Manager"
    CUSTOMER_SUPPORT_SPECIALIST = "Customer Support Specialist"
    CUSTOMER_SERVICE_ANALYST = "Customer service analyst"
    CUSTOMS_BROKER = "Customs Broker"
    CUSTOMS_OFFICER = "Customs Officer"
    CUTTER_GRINDER_POLISHER = "Cutter/Grinder/Polisher"
    DTP_OPERATOR = "DTP Operator"
    DAMAGE_APPRAISER = "Damage appraiser"
    DANCER = "Dancer"
    DATA_ENTRY_OPERATOR = "Data Entry Operator"
    DATA_PROTECTION_OFFICER = "Data Protection Officer"
    DATA_STATION_TESTING_SPECIALIST = "Data Station Testing Specialist"
    DATA_ANALYST = "Data analyst"
    DATA_COMMUNICATION_TECHNICIAN = "Data communication technician"
    DATA_SCIENTIST = "Data scientist"
    DATABASE_ADMINISTRATOR = "Database Administrator"
    DATABASE_ANALYST = "Database Analyst"
    DEALER_TRADER = "Dealer/Trader"
    DENTAL_ASSISTANT = "Dental Assistant"
    DENTAL_HYGIENIST = "Dental Hygienist"
    DENTAL_TECHNICIAN = "Dental Technician"
    DENTIST = "Dentist"
    DEPARTMENT_DIRECTOR = "Department Director"
    DEPARTMENT_MANAGER = "Department Manager"
    DEPUTY_HEADMASTER = "Deputy Headmaster"
    DEPUTY_SHOP_MANAGER = "Deputy shop manager"
    DESIGN_ENGINEER = "Design Engineer"
    DESIGN_TECHNICIAN = "Design Technician"
    DESIGN_ASSOCIATE = "Design associate"
    DESIGN_MANAGER = "Design manager"
    DESIGNER = "Designer"
    DEVELOPMENT_DIRECTOR = "Development Director"
    DEVOPS_ENGINEER = "DevOps Engineer"
    DIAGNOSTIC_TECHNICIAN = "Diagnostic Technician"
    DIGITAL_MARKETING_MANAGER = "Digital marketing manager"
    DIGITAL_MARKETING_SPECIALIST = "Digital marketing specialist"
    DISPATCH_CLERK = "Dispatch clerk"
    DISPENSING_OPTICIAN = "Dispensing Optician"
    DISTRIBUTION_CLERK = "Distribution Clerk"
    DISTRICT_FOREST_OFFICER = "District Forest Officer"
    DIVERSITY_EQUITY_AND_INCLUSION_MANAGER = "Diversity, Equity and Inclusion Manager"
    DOCTOR = "Doctor"
    DOCTOR_APPRENTICE = "Doctor apprentice"
    DRIVER = "Driver"
    DRIVING_INSTRUCTOR = "Driving Instructor"
    DRUG_SAFETY_SPECIALIST = "Drug Safety Specialist"
    E_COMMERCE_MANAGER = "E-Commerce Manager"
    E_COMMERCE_SPECIALIST = "E-Commerce Specialist"
    ERP_PROGRAMMER = "ERP programmer"
    ESG_MANAGER = "ESG manager"
    ECOLOGIST = "Ecologist"
    ECONOMIC_FINANCIAL_MANAGER = "Economic/Financial Manager"
    ECONOMIST = "Economist"
    EDITOR = "Editor"
    EDITOR_IN_CHIEF = "Editor-In-Chief"
    EDUCATION_COORDINATOR = "Education coordinator"
    EDUCATION_SPECIALIST = "Education Specialist"
    EDUCATOR_INSTRUCTOR_CARER = "Educator/Instructor/Carer"
    ELECTRICAL_ENGINEER = "Electrical Engineer"
    ELECTRICAL_ENGINEERING_TECHNICIAN = "Electrical Engineering Technician"
    ELECTRICAL_FITTER = "Electrical Fitter"
    ELECTRICIAN = "Electrician"
    ELECTRICIAN_INDUSTRIAL = "Electrician (industrial)"
    ELECTRONICS_ELECTRICIAN = "Electronics Electrician"
    ENGINE_DRIVER = "Engine Driver"
    ENVIRONMENTALIST = "Environmentalist"
    ESTATE_AGENT = "Estate Agent"
    EVENT_MANAGER = "Event Manager"
    EXPERT_SHOP_ASSISTANT = "Expert Shop Assistant"
    FABRIC_CUTTER = "Fabric Cutter"
    FACILITY_MANAGER = "Facility Manager"
    FASHION_DESIGNER_PATTERN_CUTTER = "Fashion Designer, Pattern Cutter"
    FAST_FOOD_WORKER = "Fast food worker"
    FILM_EDITOR = "Film Editor"
    FINANCE_MANAGER = "Finance Manager"
    FINANCIAL_ADVISOR = "Financial Advisor"
    FINANCIAL_AGENT = "Financial Agent"
    FINANCIAL_ANALYST = "Financial Analyst"
    FINANCIAL_MARKETS_SPECIALIST = "Financial Markets Specialist"
    FINANCIAL_ADMINISTRATION_ASSISTANT = "Financial administration assistant"
    FINISHING_WORKS_IN_CONSTRUCTIONS = "Finishing works in constructions"
    FIRE_OFFICER = "Fire Officer"
    FIREFIGHTER_RESCUER = "Firefighter, Rescuer"
    FITNESS_INSTRUCTOR = "Fitness Instructor"
    FITTER_ASSEMBLER = "Fitter/Assembler"
    FLIGHT_ATTENDANT = "Flight Attendant"
    FLOOR_LAYER_PAVER = "Floor Layer, Paver"
    FLORIST = "Florist"
    FOOD_ENGINEER = "Food Engineer"
    FOOD_TECHNICIAN = "Food Technician"
    FOOD_TECHNOLOGIST = "Food Technologist"
    FOREST_ENGINEER = "Forest Engineer"
    FOREST_TECHNICIAN = "Forest Technician"
    FORESTER = "Forester"
    FORESTRY_MANAGER = "Forestry Manager"
    FOREMAN = "Foreman"
    FORKLIFT_TRUCK_OPERATOR = "Forklift Truck Operator"
    FORWARDER = "Forwarder"
    FOUNDRY_WORKER = "Foundry worker"
    FRONTEND_DEVELOPER = "Frontend developer"
    FUNERAL_SERVICE_WORKER = "Funeral service worker"
    GAME_DESIGNER = "Game designer"
    GAME_DEVELOPER = "Game developer"
    GARDENER = "Gardener"
    GENERAL_LABOURER = "General Labourer"
    GENERAL_STATE_ADVISOR = "General State Advisor"
    GEOGRAPHIC_INFORMATION_SYSTEMS_ENGINEER = "Geographic Information Systems Engineer"
    GEOLOGIST = "Geologist"
    GEOTECHNICAL_INVESTIGATOR = "Geotechnical investigator"
    GLASSMAKER = "Glassmaker"
    GO_DEVELOPER = "Go developer"
    GOLDSMITH_JEWELLER = "Goldsmith, Jeweller"
    GRAIN_RECEIVER = "Grain Receiver"
    GRAPHIC = "Graphic"
    GRAPHIC_DESIGNER = "Graphic Designer"
    GUIDE_IN_THE_MUSEUM_GALLERY_CASTLE = "Guide in the museum, gallery, castle"
    HR_ASSISTANT = "HR Assistant"
    HR_BUSINESS_PARTNER = "HR Business Partner"
    HR_CONSULTANT = "HR Consultant"
    HR_COORDINATOR = "HR Coordinator"
    HR_GENERALIST = "HR Generalist"
    HR_MANAGER = "HR Manager"
    HR_OFFICER = "HR Officer"
    HAIRDRESSER = "Hairdresser"
    HEAD_NURSE = "Head Nurse"
    HEAD_PHARMACIST = "Head Pharmacist"
    HEAD_OF_CUSTOMER_SUPPORT = "Head of Customer Support"
    HEAD_OF_TECHNICAL_DEPARTMENT = "Head of Technical Department"
    HEAD_OF_VEHICLE_TECHNICAL_INSPECTION = "Head of Vehicle Technical Inspection"
    HEAD_OF_CONTROLLING = "Head of controlling"
    HEAD_OF_PRODUCT_DEVELOPMENT = "Head of product development"
    HEAD_OF_THE_LEGAL_DEPARTMENT = "Head of the Legal Department"
    HEALTH_CARE_ASSISTANT = "Health Care Assistant"
    HEALTH_CARE_PURCHASING_SPECIALIST = "Health Care Purchasing Specialist"
    HEALTH_PROGRAM_DEVELOPMENT_SPECIALIST = "Health Program Development Specialist"
    HEALTH_AND_SAFETY_OFFICER = "Health and Safety Officer"
    HELPDESK_OPERATOR = "Helpdesk Operator"
    HOSTESS = "Hostess"
    HOTEL_PORTER = "Hotel Porter"
    HOTEL_MANAGER = "Hotel manager"
    HOUSEKEEPER = "Housekeeper"
    HOUSEKEEPING_SUPERVISOR = "Housekeeping Supervisor"
    HOUSEMAN = "Houseman"
    IC_DESIGN_ENGINEER = "IC Design Engineer"
    ICT_SPECIALIST = "ICT Specialist"
    IFRS_SPECIALIST = "IFRS specialist"
    ISO_SPECIALIST = "ISO Specialist"
    IT_ANALYST = "IT Analyst"
    IT_ARCHITECT = "IT Architect"
    IT_BUSINESS_ANALYST = "IT Business Analyst"
    IT_CONSULTANT = "IT Consultant"
    IT_DIRECTOR = "IT Director"
    IT_MANAGER = "IT Manager"
    IT_NETWORK_ADMINISTRATOR = "IT Network Administrator"
    IT_PRODUCT_MANAGER = "IT Product Manager"
    IT_PROJECT_MANAGER = "IT Project Manager"
    IT_SECURITY_SPECIALIST = "IT Security Specialist"
    IT_SYSTEM_ADMINISTRATOR = "IT System Administrator"
    IT_TESTER = "IT Tester"
    IT_AUDITOR = "IT auditor"
    IT_TESTER_AUTOMATED_TESTS = "IT tester - automated tests"
    IT_TECHNICAL_SUPPORT_SPECIALIST = "IT/Technical Support Specialist"
    IMAGE_STYLIST_BEAUTY_STYLIST = "Image Stylist, Beauty Stylist"
    IMPORT_EXPORT_OFFICER = "Import/Export Officer"
    INCIDENT_MANAGER = "Incident manager"
    INDEPENDENT_ADVISOR = "Independent Advisor"
    INDEPENDENT_EXPERT_ASSOCIATE = "Independent Expert Associate"
    INDEPENDENT_OFFICIAL = "Independent Official"
    INDUSTRIAL_CLIMBER = "Industrial Climber"
    INDUSTRIAL_PAINTER = "Industrial painter"
    INSPECTOR = "Inspector"
    INSURANCE_BROKER = "Insurance Broker"
    INSURANCE_PAYMENT_CONTROL_SPECIALIST = "Insurance Payment Control Specialist"
    INSURANCE_TECHNICIAN = "Insurance Technician"
    INSURANCE_UNDERWRITER = "Insurance Underwriter"
    INSURANCE_ADMINISTRATOR = "Insurance administrator"
    INTERIOR_DESIGNER = "Interior Designer"
    INTERNAL_AUDITOR = "Internal Auditor"
    INTERNAL_COMMUNICATION_SPECIALIST = "Internal Communication Specialist"
    INTERPRETER = "Interpreter"
    INVOICING_AND_PAYMENT_SPECIALIST = "Invoicing and payment specialist"
    IRON_FOUNDER = "Iron founder"
    IRONWORKER = "Ironworker"
    JAVA_PROGRAMMER = "Java Programmer"
    JAVASCRIPT_PROGRAMMER = "Javascript Programmer"
    JOINER = "Joiner"
    JUDGE = "Judge"
    JUDICIAL_ASSISTANT = "Judicial assistant"
    JUNIOR_ACCOUNTANT = "Junior Accountant"
    JUNIOR_ARCHITECT = "Junior Architect"
    JUNIOR_GRAPHIC_DESIGNER = "Junior Graphic Designer"
    JUNIOR_PROJECT_MANAGER = "Junior Project Manager"
    JUNIOR_SALES_REPRESENTATIVE = "Junior Sales Representative"
    JUNIOR_STATISTICIAN = "Junior Statistician"
    KEY_ACCOUNT_MANAGER = "Key Account Manager"
    KINETOTHERAPIST = "Kinetotherapist"
    KITCHEN_DESIGNER = "Kitchen Designer"
    KITCHEN_HELPER = "Kitchen Helper"
    LABORATORY_DIRECTOR = "Laboratory Director"
    LABORATORY_TECHNICIAN = "Laboratory Technician"
    LAND_SURVEYOR_GEODESIST = "Land Surveyor/Geodesist"
    LANDSCAPE_ARCHITECT = "Landscape Architect"
    LATHE_OPERATOR = "Lathe operator"
    LABOURER = "Labourer"
    LAWYER = "Lawyer"
    LEAD_DEVELOPER = "Lead developer"
    LEASING_CONSULTANT = "Leasing Consultant"
    LEASING_DIRECTOR = "Leasing Director"
    LECTOR = "Lector"
    LECTURER_TRAINER = "Lecturer, trainer"
    LEGAL_ADVISOR = "Legal advisor"
    LIBRARIAN = "Librarian"
    LIFEGUARD_SWIMMING_INSTRUCTOR = "Lifeguard, Swimming Instructor"
    LIGHTING_TECHNICIAN = "Lighting Technician"
    LIVESTOCK_SPECIALIST = "Livestock Specialist"
    LOAN_SPECIALIST = "Loan Specialist"
    LOGISTICS_CLERK = "Logistics Clerk"
    LOGISTICS_CONTROLLER = "Logistics Controller"
    LOGISTICS_DIRECTOR = "Logistics Director"
    LOGISTICS_MANAGER = "Logistics Manager"
    LORRY_DRIVER = "Lorry Driver"
    LOSS_ADJUSTER = "Loss Adjuster"
    LUMBERJACK = "Lumberjack"
    MACHINE_FITTER = "Machine Fitter"
    MACHINE_OPERATOR = "Machine Operator"
    MACHINE_OPERATOR_MACHINIST = "Machine Operator, Machinist"
    MACHINE_SETTER = "Machine Setter"
    MAINENTENANCE_WORKER = "Mainentenance worker"
    MAINTENANCE_ENGINEER = "Maintenance Engineer"
    MAINTENANCE_SUPERVISOR = "Maintenance Supervisor"
    MAINTENANCE_WORKER = "Maintenance Worker"
    MAKE_UP_ARTIST_WIGMAKER = "Make-Up Artist, Wigmaker"
    MANAGING_DIRECTOR = "Managing Director"
    MANAGING_EDITOR = "Managing Editor"
    MARITIME_TRANSPORT_ORGANISER = "Maritime Transport Organiser"
    MARKETING_ANALYST = "Marketing Analyst"
    MARKETING_DIRECTOR = "Marketing Director"
    MARKETING_MANAGER = "Marketing Manager"
    MARKETING_OFFICER = "Marketing Officer"
    MARKETING_SPECIALIST = "Marketing Specialist"
    MARKETING_ASSISTANT = "Marketing assistant"
    MASTER_IN_VOCATIONAL_EDUCATION = "Master in Vocational Education"
    MASSEUR = "Masseur"
    MECHANICAL_DESIGN_ENGINEER_AUTOMATION = "Mechanical Design Engineer - Automation"
    MECHANICAL_ENGINEER = "Mechanical Engineer"
    MECHANIZATION_MANAGER = "Mechanization Manager"
    MEDIA_BUYER = "Media Buyer"
    MEDIA_PLANNER = "Media Planner"
    MEDICAL_ADVISOR = "Medical Advisor"
    MEDICAL_INSTITUTION_MANAGER = "Medical Institution Manager"
    MEDICAL_LABORATORY_TECHNICIAN = "Medical Laboratory Technician"
    MEDICAL_ORDERLY = "Medical Orderly"
    MEDICAL_RECORDS_CLERK = "Medical Records Clerk"
    MEDICAL_ASSISTANT = "Medical assistant"
    MEDICAL_GRADUATE = "Medical graduate"
    MEDICAL_PHARMACEUTICAL_SALES_REPRESENTATIVE = "Medical/Pharmaceutical Sales Representative"
    MECHATRONICS_TECHNICIAN = "Mechatronics Technician"
    METALLURGIST = "Metallurgist"
    METALLURGY_ENGINEER = "Metallurgy Engineer"
    METALWORKER = "Metalworker"
    METEOROLOGIST = "Meteorologist"
    METROLOGIST = "Metrologist"
    MICROBIOLOGIST = "Microbiologist"
    MICROCONTROLLER_PROGRAMMER = "Microcontroller programmer"
    MIDWIFE = "Midwife"
    MILKER = "Milker"
    MILLING_MACHINE_OPERATOR = "Milling-Machine Operator"
    MINER = "Miner"
    MINING_ENGINEER = "Mining Engineer"
    MINING_MANAGER = "Mining Manager"
    MINING_TECHNICIAN = "Mining Technician"
    MOBILE_NETWORK_DEVELOPMENT_SPECIALIST = "Mobile Network Development Specialist"
    MODEL = "Model"
    MORTGAGE_SPECIALIST = "Mortgage Specialist"
    MUSIC_AND_ART_SCHOOL_TEACHER = "Music and Art School Teacher"
    NANNY = "Nanny"
    NAVAL_OFFICER = "Naval Officer"
    NETWORK_MODELLING_SPECIALIST = "Network Modelling Specialist"
    NETWORK_STRATEGY_SPECIALIST = "Network Strategy Specialist"
    NETWORK_AND_SERVICE_OPERATION_SPECIALIST = "Network and Service Operation Specialist"
    NOTARY = "Notary"
    NOTARY_ASSOCIATE = "Notary Associate"
    NURSE = "Nurse"
    NURSERY_SCHOOL_TEACHER_ASSISTANT = "Nursery School Teacher Assistant"
    NUTRITION_ASSISTANT = "Nutrition Assistant"
    OSS_BSS_SPECIALIST = "OSS/BSS Specialist"
    OBJECTIVE_C_PROGRAMMER = "Objective-C Programmer"
    OCCUPATIONAL_PSYCHOLOGIST = "Occupational Psychologist"
    OCCUPATIONAL_HEALTH_NURSE = "Occupational health nurse"
    OFFICE_MANAGER = "Office Manager"
    OFFICIAL = "Official"
    ONLINE_SHOP_ADMINISTRATOR = "Online shop administrator"
    OPERATIONS_MANAGER = "Operations Manager"
    OPERATIONS_SUPERVISOR = "Operations Supervisor"
    OPTOMETRIST = "Optometrist"
    ORACLE_PROGRAMMER = "Oracle Programmer"
    ORGANIZER = "Organizer"
    ORTHOPEDIC_TECHNICIAN = "Orthopedic Technician"
    PHP_PROGRAMMER = "PHP Programmer"
    PLC_PROGRAMMER = "PLC Programmer"
    PPC_SPECIALIST = "PPC specialist"
    PR_MANAGER = "PR Manager"
    PC_TECHNICIAN = "PC Technician"
    PACKER = "Packer"
    PAINTER = "Painter"
    PARALEGAL_LAW_STUDENT = "Paralegal - law student"
    PASTRY_CHEF_CONFECTIONER = "Pastry Chef, Confectioner"
    PAYROLL_CLERK = "Payroll Clerk"
    PEDAGOGUE = "Pedagogue"
    PEDICURIST_MANICURIST_NAIL_TECHNICIAN = "Pedicurist, Manicurist, Nail Technician"
    PERL_PROGRAMMER = "Perl Programmer"
    PERSONAL_BANKER = "Personal Banker"
    PERSONNEL_MANAGER = "Personnel Manager"
    PETROL_STATION_ATTENDANT = "Petrol Station Attendant"
    PETROLEUM_ENGINEER = "Petroleum engineer"
    PHARMACEUTICAL_LABORATORY_TECHNICIAN = "Pharmaceutical Laboratory Technician"
    PHARMACEUTICAL_PRODUCTS_MANAGER = "Pharmaceutical Products Manager"
    PHARMACIST = "Pharmacist"
    PHARMACIST_ASSISTANT = "Pharmacist assistant"
    PHOTO_EDITOR = "Photo Editor"
    PHOTOGRAPHER = "Photographer"
    PHYSIOTHERAPIST = "Physiotherapist"
    PICKER = "Picker"
    PILOT = "Pilot"
    PIPE_FITTER = "Pipe fitter"
    PIZZA_COOK = "Pizza Cook"
    PLANNING_ASSISTANT = "Planning assistant"
    PLANT_MANAGER = "Plant manager"
    PLUMBER = "Plumber"
    POLICE_INSPECTOR = "Police Inspector"
    POLICE_OFFICER = "Police Officer"
    POSTAL_DELIVERY_WORKER = "Postal Delivery Worker"
    POSTAL_WORKER = "Postal worker"
    POSTMASTER = "Postmaster"
    POWER_ENGINEER = "Power Engineer"
    POWER_GENERATING_MACHINERY_OPERATOR = "Power-Generating Machinery Operator"
    PRE_SCHOOL_SCHOOL_KINDERGARDER_NURSE = "Pre-school/School/ Kindergarder nurse"
    PRESCHOOL_TEACHER = "Preschool Teacher"
    PRIMARY_SCHOOL_TEACHER = "Primary School Teacher"
    PRIEST = "Priest"
    PRINTER = "Printer"
    PRINTING_TECHNICIAN = "Printing Technician"
    PRISON_OFFICER = "Prison Officer"
    PRIVATE_BANKER = "Private Banker"
    PROBLEM_MANAGER = "Problem Manager"
    PROCESS_ENGINEER = "Process Engineer"
    PROCESS_MANAGER = "Process Manager"
    PROCUREMENT_SPECIALIST = "Procurement specialist"
    PRODUCER = "Producer"
    PRODUCT_DEVELOPMENT_SPECIALIST = "Product Development Specialist"
    PRODUCT_MANAGER_SPECIALIST = "Product Manager - Specialist"
    PRODUCT_MARKETING_MANAGER = "Product Marketing Manager"
    PRODUCT_OWNER = "Product owner"
    PRODUCTION_DIRECTOR = "Production Director"
    PRODUCTION_MANAGER = "Production Manager"
    PRODUCTION_PLANNER = "Production Planner"
    PRODUCTION_STANDARD_SETTER = "Production Standard Setter"
    PRODUCTION_SUPERVISOR = "Production Supervisor"
    PROFESSOR = "Professor"
    PROGRAMMER = "Programmer"
    PROJECT_ASSISTANT = "Project Assistant"
    PROJECT_COORDINATOR = "Project Coordinator"
    PROJECT_MANAGER = "Project Manager"
    PROJECT_PLANNER = "Project planner"
    PROMOTIONAL_ASSISTANT = "Promotional Assistant"
    PROOFREADER = "Proofreader"
    PROPERTY_MANAGER = "Property Manager"
    PROSECUTOR = "Prosecutor"
    PSYCHOLOGIST = "Psychologist"
    PUBLIC_HEALTH_ADMINISTRATOR = "Public Health Administrator"
    PUBLISHING_HOUSE_DIRECTOR = "Publishing House Director"
    PURCHASING_MANAGER = "Purchasing Manager"
    PYTHON_PROGRAMMER = "Python Programmer"
    QUALITY_CONTROL_ISO_MANAGER = "Quality Control/ISO Manager"
    QUALITY_ENGINEER = "Quality Engineer"
    QUALITY_INSPECTOR = "Quality Inspector"
    QUALITY_MANAGER = "Quality Manager"
    QUALITY_PLANNER = "Quality Planner"
    QUALIFIED_MECHANICAL_ENGINEER = "Qualified Mechanical Engineer"
    QUANTITY_SURVEYOR = "Quantity Surveyor"
    R_PROGRAMMER = "R programmer"
    RADIO_NETWORK_OPTIMIZATION_SPECIALIST = "Radio Network Optimization Specialist"
    RADIO_NETWORK_PLANNING_SPECIALIST = "Radio Network Planning Specialist"
    RADIO_PRESENTER_AND_ANNOUNCER = "Radio presenter and announcer"
    RADIOGRAPHER = "Radiographer"
    RADIOLOGY_ASSISTANT = "Radiology Assistant"
    RAIL_TRANSPORT_CONTROLLER_SHUNTER_SIGNALIST = "Rail Transport Controller (shunter, signalist)"
    REAL_ESTATE_APPRAISER = "Real Estate Appraiser"
    REAL_ESTATE_MAINTENANCE = "Real estate maintenance"
    RECEPTIONIST = "Receptionist"
    RECEPTIONIST_I = "Receptionist I"
    RECRUITER = "Recruiter"
    REFRIGERATION_MECHANIC = "Refrigeration Mechanic"
    REGIONAL_AREA_MANAGER = "Regional / Area Manager"
    REGIONAL_MANAGER = "Regional Manager"
    REGISTRY_ADMINISTRATION_OFFICER = "Registry Administration Officer"
    REGULATORY_AFFAIRS_MANAGER = "Regulatory Affairs Manager"
    REGULATORY_AFFAIRS_SPECIALIST = "Regulatory Affairs Specialist"
    REINSURANCE_SPECIALIST = "Reinsurance Specialist"
    RELATIONSHIP_MANAGER = "Relationship Manager"
    REPORTER = "Reporter"
    REPORTING_SPECIALIST = "Reporting Specialist"
    REPAIRER = "Repairer"
    RESEARCH_PHYSICIAN = "Research Physician"
    RESEARCH_WORKER_SCIENTIFIC_WORKER = "Research Worker, Scientific Worker"
    RESTAURANT_MANAGER = "Restaurant manager"
    RESTAURANT_WORKER = "Restaurant worker"
    RESTORER_CONSERVATOR = "Restorer/Conservator"
    RETAIL_STORE_MANAGER = "Retail Store Manager"
    RETURNS_DEPARTMENT_MANAGER = "Returns Department Manager"
    RISK_MANAGER = "Risk Manager"
    RISK_SPECIALIST = "Risk Specialist"
    ROAMING_SPECIALIST = "Roaming Specialist"
    ROOFER = "Roofer"
    RUBY_DEVELOPER_PROGRAMMER = "Ruby Developer/Programmer"
    SAP_SPECIALIST = "SAP specialist"
    SEO_ANALYST = "SEO analyst"
    SAFETY_SPECIALIST = "Safety specialist"
    SAILOR = "Sailor"
    SALES_CONSULTANT = "Sales Consultant"
    SALES_DIRECTOR = "Sales Director"
    SALES_ENGINEER = "Sales Engineer"
    SALES_MANAGER = "Sales Manager"
    SALES_OBJECT_MANAGER = "Sales Object Manager"
    SALES_OFFICE_MANAGER = "Sales Office Manager"
    SALES_OFFICER = "Sales Officer"
    SALES_REPRESENTATIVE = "Sales Representative"
    SALES_COORDINATOR = "Sales coordinator"
    SAW_FILER = "Saw filer"
    SCAFFOLDER = "Scaffolder"
    SCHOOL_CANTEEN_MANAGER = "School Canteen Manager"
    SCHOOL_CARETAKER = "School Caretaker"
    SCHOOL_PRINCIPAL = "School Principal"
    SCRUM_MASTER = "Scrum Master"
    SEAMSTRESS = "Seamstress"
    SECONDARY_SCHOOL_TEACHER = "Secondary School Teacher"
    SECRETARY = "Secretary"
    SECRETARY_OF_HEALTH_DEPARTMENT = "Secretary of health department"
    SECURITY_GUARD = "Security Guard"
    SECURITY_SERVICE_DIRECTOR = "Security Service Director"
    SECURITY_SERVICE_MANAGER = "Security Service Manager"
    SECURITY_SERVICE_TECHNICIAN = "Security service technician"
    SELLER_CASHIER = "Seller / Cashier"
    SELLER_OF_BANK_SERVICES_LOAN_OFFICER = "Seller of Bank Services, Loan Officer"
    SENIOR_ACCOUNTANT = "Senior Accountant"
    SENIOR_ASSOCIATE = "Senior Associate"
    SENIOR_GRAPHIC_DESIGNER = "Senior Graphic Designer"
    SENIOR_PROJECT_MANAGER = "Senior Project Manager"
    SENIOR_SALES_REPRESENTATIVE = "Senior Sales Representative"
    SENIOR_STATISTICIAN = "Senior Statistician"
    SERVICE_ENGINEER = "Service Engineer"
    SERVICE_TECHNICIAN = "Service Technician"
    SHELF_STACKER_MERCHANDISER = "Shelf Stacker/Merchandiser"
    SHIFT_MANAGER = "Shift manager"
    SHOP_ASSISTANT = "Shop Assistant"
    SHOP_WINDOW_DECORATOR = "Shop Window Decorator"
    SMITH = "Smith"
    SOCIAL_COUNSELOR = "Social counselor"
    SOCIAL_MEDIA_SPECIALIST = "Social media specialist"
    SOCIAL_REHABILITATION_SPECIALIST = "Social rehabilitation specialist"
    SOFTWARE_ENGINEER = "Software Engineer"
    SOFTWARE_CONSULTANT = "Software consultant"
    SOLDIER = "Soldier"
    SOLICITOR_BARRISTER = "Solicitor, Barrister"
    SOMMELIER = "Sommelier"
    SOUND_ENGINEER = "Sound Engineer"
    SPA_THERAPIST = "Spa Therapist"
    SPATIAL_PLANNER = "Spatial Planner"
    SPECIAL_NEEDS_TEACHER = "Special Needs Teacher"
    SPECIALIST_ADVISOR = "Specialist Advisor"
    SPECIALIST_OFFICIAL = "Specialist Official"
    SPEECH_THERAPIST = "Speech Therapist"
    SPORTS_COACH = "Sports Coach"
    SPORTS_COORDINATOR = "Sports Coordinator"
    STAGEHAND = "Stagehand"
    STATE_ADVISOR = "State Advisor"
    STOCK_BROKER = "Stock Broker"
    STOKER_BOILER_ATTENDANT = "Stoker, Boiler Attendant"
    STONEMASON = "Stonemason"
    STORE_DEPARTMENT_MANAGER = "Store Department Manager"
    STOREKEEPER = "Storekeeper"
    STRUCTURAL_ENGINEER = "Structural Engineer"
    SUPERINTENDENT = "Superintendent"
    SUPPLY_CHAIN_SPECIALIST = "Supply Chain Specialist"
    SUPPLY_TECHNICIAN = "Supply Technician"
    SURVEY_INTERVIEWER = "Survey Interviewer"
    SWITCHING_NETWORK_DEVELOPMENT_SPECIALIST = "Switching Network Development Specialist"
    SYSTEMS_ADMINISTRATOR = "Systems Administrator"
    SYSTEMS_ENGINEER = "Systems Engineer"
    TV_PRESENTER = "TV Presenter"
    TV_FILM_PRODUCTION_ASSISTANT = "TV/Film Production Assistant"
    TAILOR = "Tailor"
    TAX_ADVISOR = "Tax Advisor"
    TAXI_DRIVER = "Taxi driver"
    TEACHER = "Teacher"
    TEAM_LEADER = "Team leader"
    TECHNICAL_DIRECTOR = "Technical Director"
    TECHNICAL_MANAGER = "Technical Manager"
    TECHNICAL_STAFF = "Technical Staff"
    TECHNICAL_SUPPORT_SPECIALIST = "Technical Support Specialist"
    TECHNICAL_WRITER = "Technical Writer"
    TECHNICAL_PRODUCT_ENGINEER = "Technical product engineer"
    TELECOMMUNICATION_SPECIALIST = "Telecommunication Specialist"
    TELECOMMUNICATION_NETWORK_INSTALLER = "Telecommunication network installer"
    TELECOMMUNICATIONS_NETWORK_DESIGNER = "Telecommunications Network Designer"
    TELECOMMUNICATIONS_PRODUCT_DEVELOPMENT_SPECIALIST = "Telecommunications Product Development Specialist"
    TELECOMMUNICATIONS_SERVICE_DEVELOPMENT_SPECIALIST = "Telecommunications Service Development Specialist"
    TELEMARKETER = "Telemarketer"
    TERMINAL_OPERATOR = "Terminal operator"
    TESTING_MANAGER = "Testing manager"
    TECHNICIAN = "Technician"
    TECHNOLOGIST = "Technologist"
    TILE_MAN = "Tile man"
    TIMBER_ENGINEER = "Timber Engineer"
    TOOLMAKER = "Toolmaker"
    TRAFFIC_CONTROLLER = "Traffic Controller"
    TRAFFIC_ENGINEER = "Traffic Engineer"
    TRAIN_CONDUCTOR = "Train Conductor"
    TRAIN_DISPATCHER = "Train Dispatcher"
    TRAINEE_BAILIFF = "Trainee Bailiff"
    TRAM_DRIVER = "Tram Driver"
    TRANSMISSION_NETW_ANALYSIS_DEVELOPMENT_SPECIALIST = "Transmission Netw. Analysis&Development Specialist"
    TRANSPORT_MANAGER = "Transport manager"
    TRAVEL_GUIDE = "Travel Guide"
    TROLLEYBUS_DRIVER = "Trolleybus Driver"
    TUTOR = "Tutor"
    TYRE_FITTER = "Tyre Fitter"
    UX_DESIGNER = "UX designer"
    UNIVERSITY_TEACHER = "University Teacher"
    UNIVERSITY_TEACHING_ASSISTANT = "University Teaching assistant"
    UPHOLSTERER = "Upholsterer"
    USER_EXPERIENCE_EXPERT = "User Experience Expert"
    VAT_SPECIALIST = "VAT specialist"
    VFX_ARTIST = "VFX artist"
    VARNISHER = "Varnisher"
    VEHICLE_BODY_REPAIRER = "Vehicle Body Repairer"
    VETERINARIAN = "Veterinarian"
    VETERINARY_TECHNICIAN = "Veterinary Technician"
    VISUAL_MERCHANDISER = "Visual merchandiser"
    WAITER = "Waiter"
    WAITER_ROOM_SERVICE = "Waiter - Room Service"
    WARD_DOMESTIC = "Ward domestic"
    WARDROBE_ASSISTANT = "Wardrobe Assistant"
    WAREHOUSE_MANAGER = "Warehouse Manager"
    WAREHOUSEMAN = "Warehouseman"
    WATER_MANAGEMENT_ENGINEER = "Water Management Engineer"
    WATER_MANAGEMENT_TECHNICIAN = "Water Management Technician"
    WEB_DESIGNER = "Web Designer"
    WEBMASTER = "Webmaster"
    WELDER = "Welder"
    WINDOW_DRESSER_DECORATOR = "Window Dresser, Decorator"
    WOODWORKING_TECHNICIAN = "Woodworking Technician"
    YOUTH_WORKER = "Youth worker"
    IOS_DEVELOPER = "iOS Developer"
    OTHER = "Other"

    @classmethod
    @lru_cache(maxsize=1)
    def _mongolian_names(cls) -> dict[PositionalCategory, str]:
        return {
            cls.NET_PROGRAMMER: ".NET программист",
            cls.ABAP_PROGRAMMER: "ABAP программист",
            cls.AI_ENGINEER: "Хиймэл оюун ухааны инженер",
            cls.ASP_NET_PROGRAMMER: "ASP.NET программист",
            cls.ACCOUNT_DIRECTOR: "Дансны захирал",
            cls.ACCOUNT_EXECUTIVE: "Дансны гүйцэтгэх ажилтан",
            cls.ACCOUNT_MANAGER: "Дансны менежер",
            cls.ACCOUNTANT: "Нягтлан бодогч",
            cls.ACCOUNTING_CLERK: "Нягтлан бодох бүртгэлийн ажилтан",
            cls.ACCOUNTING_SERVICE_MANAGER: "Нягтлан бодох бүртгэлийн үйлчилгээний менежер",
            cls.ACCOMMODATION_MANAGER: "Байрны менежер",
            cls.ACTOR: "Жүжигчин",
            cls.ACTIVITY_INSTRUCTOR: "Үйл ажиллагааны зааварлагч",
            cls.ADMINISTRATIVE_WORKER: "Захиргааны ажилтан",
            cls.ADMINISTRATIVE_OFFICER: "Захиргааны офицер",
            cls.AGRICULTURAL_ENGINEER_AGRONOMIST: "Хөдөө аж ахуйн инженер, Агрономч",
            cls.AGRICULTURAL_EQUIPMENT_OPERATOR: "Хөдөө аж ахуйн тоног төхөөрөмжийн оператор",
            cls.AGRICULTURAL_SPECIALIST: "Хөдөө аж ахуйн мэргэжилтэн",
            cls.AGRICULTURAL_TECHNICIAN: "Хөдөө аж ахуйн техникч",
            cls.AGRICULTURAL_TECHNOLOGIST: "Хөдөө аж ахуйн технологич",
            cls.AIR_TRAFFIC_CONTROLLER: "Агаарын хөдөлгөөний хяналтын ажилтан",
            cls.AIRCRAFT_TECHNICIAN: "Нисэх онгоцны техникч",
            cls.AIRCRAFT_ENGINEER: "Нисэх онгоцны инженер",
            cls.AMBULANCE_DRIVER: "Түргэн тусламжийн жолооч",
            cls.AMBULANCE_PARAMEDIC: "Түргэн тусламжийн парамедик",
            cls.ANESTHETIST: "Мэдээ алдуулагч эмч",
            cls.ANIMAL_CARE_WORKER: "Амьтны асаргааны ажилтан",
            cls.ANTI_MONEY_LAUNDERING_SPECIALIST: "Мөнгө угаахтай тэмцэх мэргэжилтэн",
            cls.ARCHAEOLOGIST: "Археологич",
            cls.ARCHITECT: "Архитектор",
            cls.ART_DIRECTOR: "Урлагийн захирал",
            cls.ARCHIVIST_REGISTRY_ADMINISTRATOR: "Архивч, Бүртгэлийн администратор",
            cls.ASSISTANT: "Туслах",
            cls.ASSISTANT_COOK: "Тогооч туслах",
            cls.ASSISTANT_FINANCIAL_CONTROLLER: "Санхүүгийн хяналтын туслах",
            cls.ASSISTANT_TEACHER: "Багшийн туслах",
            cls.ASSISTANT_OF_AUDITOR: "Аудиторын туслах",
            cls.ASSISTANT_TO_A_TAX_ADVISOR: "Татварын зөвлөхийн туслах",
            cls.AU_PAIR: "Ау-пэйр",
            cls.AUDITOR: "Аудитор",
            cls.AUTO_ELECTRICIAN: "Автомашины цахилгаанч",
            cls.AUTO_REPAIR_SHOP_MANAGER: "Автомашины засварын газрын менежер",
            cls.AUTOMATION_ENGINEER: "Автоматжуулалтын инженер",
            cls.AUTOMATION_PLANNER: "Автоматжуулалтын төлөвлөгч",
            cls.AXEMAN: "Сүхчин",
            cls.BACK_OFFICE_SPECIALIST: "Арын оффисын мэргэжилтэн",
            cls.BAILIFF_ENFORCEMENT_OFFICER: "Шүүхийн биелэлтийн ажилтан",
            cls.BAKER: "Талхчин",
            cls.BARTENDER: "Бартендер",
            cls.BEAUTICIAN: "Гоо сайханч",
            cls.BETTING_CLERK: "Бооцооны ажилтан",
            cls.BICYCLE_MECHANIC: "Дугуйн механик",
            cls.BIDDING_ENGINEER: "Тендерийн инженер",
            cls.BILLING_CLERK: "Тооцооны ажилтан",
            cls.BIOLOGIST: "Биологич",
            cls.BOOKBINDER: "Номын хавтасч",
            cls.BOOKMAKER: "Бооцооны компанийн ажилтан",
            cls.BOOKING_AGENT: "Захиалгын агент",
            cls.BOSUN: "Хөлөг онгоцны ахлагч",
            cls.BRANCH_DIRECTOR: "Салбарын захирал",
            cls.BRAND_MANAGER: "Брэндийн менежер",
            cls.BRICKLAYER: "Тоосгочин",
            cls.BUILDING_CONTROL_SURVEYOR: "Барилгын хяналтын хэмжигч",
            cls.BUILDING_TECHNICIAN: "Барилгын техникч",
            cls.BUS_DRIVER: "Автобусны жолооч",
            cls.BUSINESS_ANALYST: "Бизнес шинжээч",
            cls.BUSINESS_DEVELOPMENT_MANAGER: "Бизнесийн хөгжлийн менежер",
            cls.BUSINESS_GROUP_MANAGER: "Бизнесийн бүлгийн менежер",
            cls.BUSINESS_INTELLIGENCE_SPECIALIST: "Бизнесийн тагнуулын мэргэжилтэн",
            cls.BUTCHER: "Махчин",
            cls.BUYING_AGENT: "Худалдан авалтын агент",
            cls.C_PROGRAMMER: "C программист",
            cls.CSHARP_PROGRAMMER: "C# программист",
            cls.CPP_PROGRAMMER: "C++ программист",
            cls.CAD_SPECIALIST: "CAD мэргэжилтэн",
            cls.CNC_MACHINE_SETTER: "CNC машины тохируулагч",
            cls.CNC_PROGRAMMER: "CNC программист",
            cls.CRM_SPECIALIST: "CRM мэргэжилтэн",
            cls.CSR_SPECIALIST: "CSR мэргэжилтэн",
            cls.CABINET_MAKER: "Тавилгачин",
            cls.CABLE_CAR_OPERATOR: "Кабины машины оператор",
            cls.CALL_CENTER_SUPERVISOR: "Дуудлагын төвийн ахлагч",
            cls.CALL_CENTRE_DIRECTOR: "Дуудлагын төвийн захирал",
            cls.CALL_CENTRE_MANAGER: "Дуудлагын төвийн менежер",
            cls.CALL_OPERATOR: "Дуудлагын оператор",
            cls.CAMERA_OPERATOR: "Камерын оператор",
            cls.CAR_DRIVER: "Автомашины жолооч",
            cls.CAR_FLEET_MANAGER: "Автопаркын менежер",
            cls.CAR_GLASS_FITTER: "Автомашины шилний угсрагч",
            cls.CAR_MECHANIC: "Автомашины механик",
            cls.CAR_UPHOLSTERER: "Автомашины эдлэлчин",
            cls.CAR_WASH_WORKER: "Автомашин угаагч",
            cls.CAR_SALESMAN: "Автомашины худалдагч",
            cls.CAREER_ADVISOR: "Карьерын зөвлөх",
            cls.CAREGIVER: "Асрагч",
            cls.CARER_PERSONAL_ASSISTANT: "Асрагч, Хувийн туслах",
            cls.CARPENTER: "Мужаан",
            cls.CASEWORKER: "Хэргийн ажилтан",
            cls.CASHIER: "Кассир",
            cls.CATERING_MANAGER: "Хоолны үйлчилгээний менежер",
            cls.CHAMBERMAID: "Өрөөний үйлчлэгч",
            cls.CHARGE_NURSE: "Ахлах сувилагч",
            cls.CHEMICAL_ENGINEER: "Химийн инженер",
            cls.CHEMICAL_LAB_TECHNICIAN: "Химийн лабораторийн техникч",
            cls.CHEMIST: "Химич",
            cls.CHEF: "Ерөнхий тогооч",
            cls.CHIEF_ACCOUNTANT: "Ерөнхий нягтлан бодогч",
            cls.CHIEF_ACCOUNTANT_DEPUTY: "Ерөнхий нягтлан бодогчийн орлогч",
            cls.CHIEF_ADVISOR: "Ерөнхий зөвлөх",
            cls.CHIEF_EXECUTIVE_OFFICER: "Гүйцэтгэх захирал",
            cls.CHIEF_OFFICIAL: "Ерөнхий албан тушаалтан",
            cls.CHIEF_RECEPTIONIST_OFFICER: "Ерөнхий хүлээн авалтын ажилтан",
            cls.CHIEF_STATE_ADVISOR: "Улсын ерөнхий зөвлөх",
            cls.CHIEF_BOROUGH_CONTROLLER: "Дүүргийн ерөнхий хяналтын ажилтан",
            cls.CHOREOGRAPHER: "Хореограф",
            cls.CIVIL_ENGINEER: "Иргэний инженер",
            cls.CLAIMS_ADMINISTRATOR: "Нэхэмжлэлийн администратор",
            cls.CLAIMS_SPECIALIST: "Нэхэмжлэлийн мэргэжилтэн",
            cls.CLEANER: "Цэвэрлэгч",
            cls.CLEANING_MANAGER: "Цэвэрлэгээний менежер",
            cls.CLIENT_OFFICER: "Үйлчлүүлэгчийн ажилтан",
            cls.CLINICAL_DATA_MANAGER: "Клиникийн өгөгдлийн менежер",
            cls.CLINICAL_PSYCHOLOGIST: "Клиникийн сэтгэл зүйч",
            cls.CLINICAL_RESEARCH_ASSOCIATE: "Клиникийн судалгааны нэгдэл",
            cls.CLOTHING_TEXTILE_TECHNOLOGIST: "Хувцас/нэхмэлийн технологич",
            cls.COACH: "Дасгалжуулагч",
            cls.CO_ORDINATOR: "Зохицуулагч",
            cls.COBBLER: "Гуталчин",
            cls.COLLEGE_LECTOR: "Коллежийн лектор",
            cls.COMPLAINTS_DEPARTMENT_CLERK: "Гомдлын хэлтсийн ажилтан",
            cls.COMPLIANCE_SPECIALIST: "Дагаж мөрдөх мэргэжилтэн",
            cls.COMPENSATION_BENEFIT_SPECIALIST: "Нөхөн олговор ба тэтгэмжийн мэргэжилтэн",
            cls.CONCIERGE: "Консьерж",
            cls.CONSTRUCTION_MANAGER: "Барилгын менежер",
            cls.CONSTRUCTION_PLANT_OPERATOR: "Барилгын тоног төхөөрөмжийн оператор",
            cls.CONSTRUCTION_WORKER: "Барилгын ажилтан",
            cls.CONSULTANT: "Зөвлөх",
            cls.CONTENT_PROVIDER: "Контент нийлүүлэгч",
            cls.CONTRACT_ADMINISTRATOR: "Гэрээний администратор",
            cls.CONTROLLER: "Хянагч",
            cls.COOK: "Тогооч",
            cls.COPYWRITER: "Копирайтер",
            cls.COST_ACCOUNTANT: "Зардлын нягтлан бодогч",
            cls.COUNTER_CLERK: "Лавлагааны ажилтан",
            cls.COUNTRY_MANAGER_DIRECTOR: "Улсын менежер/захирал",
            cls.COURIER: "Курьер",
            cls.CRANE_OPERATOR: "Кран оператор",
            cls.CRISIS_WORKER: "Хямралын ажилтан",
            cls.CROUPIER: "Крупье",
            cls.CULTURAL_OFFICER: "Соёлын ажилтан",
            cls.CURATOR: "Куратор",
            cls.CUSTOMER_RELATIONSHIP_MANAGER: "Үйлчлүүлэгчтэй харилцах менежер",
            cls.CUSTOMER_SUPPORT_SPECIALIST: "Үйлчлүүлэгчийн дэмжлэгийн мэргэжилтэн",
            cls.CUSTOMER_SERVICE_ANALYST: "Үйлчлүүлэгчийн үйлчилгээний шинжээч",
            cls.CUSTOMS_BROKER: "Гаалийн брокер",
            cls.CUSTOMS_OFFICER: "Гаалийн ажилтан",
            cls.CUTTER_GRINDER_POLISHER: "Огтолч/Зүлгүүрч/Гялалгаагч",
            cls.DTP_OPERATOR: "DTP оператор",
            cls.DAMAGE_APPRAISER: "Хохирол үнэлгээч",
            cls.DANCER: "Бүжигчин",
            cls.DATA_ENTRY_OPERATOR: "Өгөгдөл оруулагч оператор",
            cls.DATA_PROTECTION_OFFICER: "Өгөгдөл хамгаалалтын ажилтан",
            cls.DATA_STATION_TESTING_SPECIALIST: "Өгөгдлийн станцын туршилтын мэргэжилтэн",
            cls.DATA_ANALYST: "Өгөгдлийн шинжээч",
            cls.DATA_COMMUNICATION_TECHNICIAN: "Өгөгдлийн харилцааны техникч",
            cls.DATA_SCIENTIST: "Өгөгдлийн эрдэмтэн",
            cls.DATABASE_ADMINISTRATOR: "Мэдээллийн сангийн администратор",
            cls.DATABASE_ANALYST: "Мэдээллийн сангийн шинжээч",
            cls.DEALER_TRADER: "Дилер/Трейдер",
            cls.DENTAL_ASSISTANT: "Шүдний эмчийн туслах",
            cls.DENTAL_HYGIENIST: "Шүдний эрүүл ахуйн мэргэжилтэн",
            cls.DENTAL_TECHNICIAN: "Шүдний техникч",
            cls.DENTIST: "Шүдний эмч",
            cls.DEPARTMENT_DIRECTOR: "Хэлтсийн захирал",
            cls.DEPARTMENT_MANAGER: "Хэлтсийн менежер",
            cls.DEPUTY_HEADMASTER: "Захирлын орлогч",
            cls.DEPUTY_SHOP_MANAGER: "Дэлгүүрийн менежерийн орлогч",
            cls.DESIGN_ENGINEER: "Зураг төслийн инженер",
            cls.DESIGN_TECHNICIAN: "Зураг төслийн техникч",
            cls.DESIGN_ASSOCIATE: "Зураг төслийн нэгдэл",
            cls.DESIGN_MANAGER: "Зураг төслийн менежер",
            cls.DESIGNER: "Дизайнер",
            cls.DEVELOPMENT_DIRECTOR: "Хөгжлийн захирал",
            cls.DEVOPS_ENGINEER: "DevOps инженер",
            cls.DIAGNOSTIC_TECHNICIAN: "Оношлогооны техникч",
            cls.DIGITAL_MARKETING_MANAGER: "Дижитал маркетингийн менежер",
            cls.DIGITAL_MARKETING_SPECIALIST: "Дижитал маркетингийн мэргэжилтэн",
            cls.DISPATCH_CLERK: "Диспетчерийн ажилтан",
            cls.DISPENSING_OPTICIAN: "Нүдний шилний мэргэжилтэн",
            cls.DISTRIBUTION_CLERK: "Түгээлтийн ажилтан",
            cls.DISTRICT_FOREST_OFFICER: "Дүүргийн ойн ажилтан",
            cls.DIVERSITY_EQUITY_AND_INCLUSION_MANAGER: "Олон талт байдал, Тэгш байдал ба Оролцооны менежер",
            cls.DOCTOR: "Эмч",
            cls.DOCTOR_APPRENTICE: "Эмчийн шавь",
            cls.DRIVER: "Жолооч",
            cls.DRIVING_INSTRUCTOR: "Жолооны сургалтын багш",
            cls.DRUG_SAFETY_SPECIALIST: "Эмийн аюулгүй байдлын мэргэжилтэн",
            cls.E_COMMERCE_MANAGER: "Цахим худалдааны менежер",
            cls.E_COMMERCE_SPECIALIST: "Цахим худалдааны мэргэжилтэн",
            cls.ERP_PROGRAMMER: "ERP программист",
            cls.ESG_MANAGER: "ESG менежер",
            cls.ECOLOGIST: "Экологич",
            cls.ECONOMIC_FINANCIAL_MANAGER: "Эдийн засаг/санхүүгийн менежер",
            cls.ECONOMIST: "Эдийн засагч",
            cls.EDITOR: "Редактор",
            cls.EDITOR_IN_CHIEF: "Ерөнхий редактор",
            cls.EDUCATION_COORDINATOR: "Боловсролын зохицуулагч",
            cls.EDUCATION_SPECIALIST: "Боловсролын мэргэжилтэн",
            cls.EDUCATOR_INSTRUCTOR_CARER: "Боловсролч/Зааварлагч/Асрагч",
            cls.ELECTRICAL_ENGINEER: "Цахилгааны инженер",
            cls.ELECTRICAL_ENGINEERING_TECHNICIAN: "Цахилгааны инженерийн техникч",
            cls.ELECTRICAL_FITTER: "Цахилгааны угсрагч",
            cls.ELECTRICIAN: "Цахилгаанч",
            cls.ELECTRICIAN_INDUSTRIAL: "Цахилгаанч (үйлдвэрийн)",
            cls.ELECTRONICS_ELECTRICIAN: "Электроникийн цахилгаанч",
            cls.ENGINE_DRIVER: "Хөдөлгүүрийн жолооч",
            cls.ENVIRONMENTALIST: "Байгаль орчны мэргэжилтэн",
            cls.ESTATE_AGENT: "Үл хөдлөх хөрөнгийн агент",
            cls.EVENT_MANAGER: "Арга хэмжээний менежер",
            cls.EXPERT_SHOP_ASSISTANT: "Мэргэжлийн дэлгүүрийн туслах",
            cls.FABRIC_CUTTER: "Даавуу огтолч",
            cls.FACILITY_MANAGER: "Байгууламжийн менежер",
            cls.FASHION_DESIGNER_PATTERN_CUTTER: "Загварч, Загварын огтолч",
            cls.FAST_FOOD_WORKER: "Хурдан хоолны ажилтан",
            cls.FILM_EDITOR: "Киноны редактор",
            cls.FINANCE_MANAGER: "Санхүүгийн менежер",
            cls.FINANCIAL_ADVISOR: "Санхүүгийн зөвлөх",
            cls.FINANCIAL_AGENT: "Санхүүгийн агент",
            cls.FINANCIAL_ANALYST: "Санхүүгийн шинжээч",
            cls.FINANCIAL_MARKETS_SPECIALIST: "Санхүүгийн зах зээлийн мэргэжилтэн",
            cls.FINANCIAL_ADMINISTRATION_ASSISTANT: "Санхүүгийн захиргааны туслах",
            cls.FINISHING_WORKS_IN_CONSTRUCTIONS: "Барилгын дуусгалтын ажил",
            cls.FIRE_OFFICER: "Гал түймэрийн ажилтан",
            cls.FIREFIGHTER_RESCUER: "Гал унтраагч, Аврагч",
            cls.FITNESS_INSTRUCTOR: "Фитнессийн зааварлагч",
            cls.FITTER_ASSEMBLER: "Угсрагч",
            cls.FLIGHT_ATTENDANT: "Нислэгийн бүртгэгч",
            cls.FLOOR_LAYER_PAVER: "Шалны тавигч",
            cls.FLORIST: "Цэцгийн дэлгүүрийн ажилтан",
            cls.FOOD_ENGINEER: "Хүнсний инженер",
            cls.FOOD_TECHNICIAN: "Хүнсний техникч",
            cls.FOOD_TECHNOLOGIST: "Хүнсний технологич",
            cls.FOREST_ENGINEER: "Ойн инженер",
            cls.FOREST_TECHNICIAN: "Ойн техникч",
            cls.FORESTER: "Ойч",
            cls.FORESTRY_MANAGER: "Ойн аж ахуйн менежер",
            cls.FOREMAN: "Ахлах ажилтан",
            cls.FORKLIFT_TRUCK_OPERATOR: "Форклифтийн оператор",
            cls.FORWARDER: "Экспедитор",
            cls.FOUNDRY_WORKER: "Цутгалтын ажилтан",
            cls.FRONTEND_DEVELOPER: "Фронтэнд хөгжүүлэгч",
            cls.FUNERAL_SERVICE_WORKER: "Оршуулгын үйлчилгээний ажилтан",
            cls.GAME_DESIGNER: "Тоглоомын дизайнер",
            cls.GAME_DEVELOPER: "Тоглоомын хөгжүүлэгч",
            cls.GARDENER: "Цэцэрлэгч",
            cls.GENERAL_LABOURER: "Ерөнхий хөдөлмөрчин",
            cls.GENERAL_STATE_ADVISOR: "Улсын ерөнхий зөвлөх",
            cls.GEOGRAPHIC_INFORMATION_SYSTEMS_ENGINEER: "Газарзүйн мэдээллийн системийн инженер",
            cls.GEOLOGIST: "Геологич",
            cls.GEOTECHNICAL_INVESTIGATOR: "Геотехникийн судлаач",
            cls.GLASSMAKER: "Шилчин",
            cls.GO_DEVELOPER: "Go хөгжүүлэгч",
            cls.GOLDSMITH_JEWELLER: "Алтны дархан, Үнэт эдлэлч",
            cls.GRAIN_RECEIVER: "Үр тарианы хүлээн авагч",
            cls.GRAPHIC: "График",
            cls.GRAPHIC_DESIGNER: "График дизайнер",
            cls.GUIDE_IN_THE_MUSEUM_GALLERY_CASTLE: "Музей, галерей, цайзны хөтөч",
            cls.HR_ASSISTANT: "Хүний нөөцийн туслах",
            cls.HR_BUSINESS_PARTNER: "Хүний нөөцийн бизнес түнш",
            cls.HR_CONSULTANT: "Хүний нөөцийн зөвлөх",
            cls.HR_COORDINATOR: "Хүний нөөцийн зохицуулагч",
            cls.HR_GENERALIST: "Хүний нөөцийн ерөнхий мэргэжилтэн",
            cls.HR_MANAGER: "Хүний нөөцийн менежер",
            cls.HR_OFFICER: "Хүний нөөцийн ажилтан",
            cls.HAIRDRESSER: "Үсчин",
            cls.HEAD_NURSE: "Ахлах сувилагч",
            cls.HEAD_PHARMACIST: "Ахлах эм зүйч",
            cls.HEAD_OF_CUSTOMER_SUPPORT: "Үйлчлүүлэгчийн дэмжлэгийн дарга",
            cls.HEAD_OF_TECHNICAL_DEPARTMENT: "Техникийн хэлтсийн дарга",
            cls.HEAD_OF_VEHICLE_TECHNICAL_INSPECTION: "Тээврийн хэрэгслийн техникийн үзлэгийн дарга",
            cls.HEAD_OF_CONTROLLING: "Хяналтын хэлтсийн дарга",
            cls.HEAD_OF_PRODUCT_DEVELOPMENT: "Бүтээгдэхүүн хөгжүүлэлтийн дарга",
            cls.HEAD_OF_THE_LEGAL_DEPARTMENT: "Хуулийн хэлтсийн дарга",
            cls.HEALTH_CARE_ASSISTANT: "Эрүүл мэндийн тусламжийн ажилтан",
            cls.HEALTH_CARE_PURCHASING_SPECIALIST: "Эрүүл мэндийн худалдан авалтын мэргэжилтэн",
            cls.HEALTH_PROGRAM_DEVELOPMENT_SPECIALIST: "Эрүүл мэндийн хөтөлбөр хөгжүүлэлтийн мэргэжилтэн",
            cls.HEALTH_AND_SAFETY_OFFICER: "Эрүүл мэнд, Аюулгүй байдлын ажилтан",
            cls.HELPDESK_OPERATOR: "Тусламжийн ширээний оператор",
            cls.HOSTESS: "Хостесс",
            cls.HOTEL_PORTER: "Зочид буудлын портье",
            cls.HOTEL_MANAGER: "Зочид буудлын менежер",
            cls.HOUSEKEEPER: "Гэрийн үйлчлэгч",
            cls.HOUSEKEEPING_SUPERVISOR: "Гэр ахуйн ажлын ахлагч",
            cls.HOUSEMAN: "Гэрийн ажилтан",
            cls.IC_DESIGN_ENGINEER: "IC зураг төслийн инженер",
            cls.ICT_SPECIALIST: "МХТ-ийн мэргэжилтэн",
            cls.IFRS_SPECIALIST: "НББОУС-ийн мэргэжилтэн",
            cls.ISO_SPECIALIST: "ISO мэргэжилтэн",
            cls.IT_ANALYST: "МТ-ийн шинжээч",
            cls.IT_ARCHITECT: "МТ-ийн архитектор",
            cls.IT_BUSINESS_ANALYST: "МТ-ийн бизнес шинжээч",
            cls.IT_CONSULTANT: "МТ-ийн зөвлөх",
            cls.IT_DIRECTOR: "МТ-ийн захирал",
            cls.IT_MANAGER: "МТ-ийн менежер",
            cls.IT_NETWORK_ADMINISTRATOR: "МТ-ийн сүлжээний администратор",
            cls.IT_PRODUCT_MANAGER: "МТ-ийн бүтээгдэхүүний менежер",
            cls.IT_PROJECT_MANAGER: "МТ-ийн төслийн менежер",
            cls.IT_SECURITY_SPECIALIST: "МТ-ийн аюулгүй байдлын мэргэжилтэн",
            cls.IT_SYSTEM_ADMINISTRATOR: "МТ-ийн системийн администратор",
            cls.IT_TESTER: "МТ-ийн тестер",
            cls.IT_AUDITOR: "МТ-ийн аудитор",
            cls.IT_TESTER_AUTOMATED_TESTS: "МТ-ийн тестер - автомат тест",
            cls.IT_TECHNICAL_SUPPORT_SPECIALIST: "МТ/Техникийн дэмжлэгийн мэргэжилтэн",
            cls.IMAGE_STYLIST_BEAUTY_STYLIST: "Дүр төрхийн стилист, Гоо сайханы стилист",
            cls.IMPORT_EXPORT_OFFICER: "Импорт/экспортын ажилтан",
            cls.INCIDENT_MANAGER: "Аваарын менежер",
            cls.INDEPENDENT_ADVISOR: "Бие даасан зөвлөх",
            cls.INDEPENDENT_EXPERT_ASSOCIATE: "Бие даасан мэргэжилтэн",
            cls.INDEPENDENT_OFFICIAL: "Бие даасан албан тушаалтан",
            cls.INDUSTRIAL_CLIMBER: "Үйлдвэрийн альпинист",
            cls.INDUSTRIAL_PAINTER: "Үйлдвэрийн будагч",
            cls.INSPECTOR: "Байцаагч",
            cls.INSURANCE_BROKER: "Даатгалын брокер",
            cls.INSURANCE_PAYMENT_CONTROL_SPECIALIST: "Даатгалын төлбөрийн хяналтын мэргэжилтэн",
            cls.INSURANCE_TECHNICIAN: "Даатгалын техникч",
            cls.INSURANCE_UNDERWRITER: "Даатгалын андеррайтер",
            cls.INSURANCE_ADMINISTRATOR: "Даатгалын администратор",
            cls.INTERIOR_DESIGNER: "Интерьер дизайнер",
            cls.INTERNAL_AUDITOR: "Дотоод аудитор",
            cls.INTERNAL_COMMUNICATION_SPECIALIST: "Дотоод харилцааны мэргэжилтэн",
            cls.INTERPRETER: "Орчуулагч",
            cls.INVOICING_AND_PAYMENT_SPECIALIST: "Нэхэмжлэх, Төлбөрийн мэргэжилтэн",
            cls.IRON_FOUNDER: "Төмрийн цутгагч",
            cls.IRONWORKER: "Төмөрчин",
            cls.JAVA_PROGRAMMER: "Java программист",
            cls.JAVASCRIPT_PROGRAMMER: "Javascript программист",
            cls.JOINER: "Модон эдлэлчин",
            cls.JUDGE: "Шүүгч",
            cls.JUDICIAL_ASSISTANT: "Шүүхийн туслах",
            cls.JUNIOR_ACCOUNTANT: "Дэд нягтлан бодогч",
            cls.JUNIOR_ARCHITECT: "Дэд архитектор",
            cls.JUNIOR_GRAPHIC_DESIGNER: "Дэд график дизайнер",
            cls.JUNIOR_PROJECT_MANAGER: "Дэд төслийн менежер",
            cls.JUNIOR_SALES_REPRESENTATIVE: "Дэд борлуулалтын төлөөлөгч",
            cls.JUNIOR_STATISTICIAN: "Дэд статистикч",
            cls.KEY_ACCOUNT_MANAGER: "Гол дансны менежер",
            cls.KINETOTHERAPIST: "Кинетотерапевт",
            cls.KITCHEN_DESIGNER: "Гал тогооны дизайнер",
            cls.KITCHEN_HELPER: "Гал тогооны туслах",
            cls.LABORATORY_DIRECTOR: "Лабораторийн захирал",
            cls.LABORATORY_TECHNICIAN: "Лабораторийн техникч",
            cls.LAND_SURVEYOR_GEODESIST: "Газрын хэмжигч/Геодезист",
            cls.LANDSCAPE_ARCHITECT: "Ландшафтын архитектор",
            cls.LATHE_OPERATOR: "Токарь оператор",
            cls.LABOURER: "Хөдөлмөрчин",
            cls.LAWYER: "Хуульч",
            cls.LEAD_DEVELOPER: "Ахлах хөгжүүлэгч",
            cls.LEASING_CONSULTANT: "Лизингийн зөвлөх",
            cls.LEASING_DIRECTOR: "Лизингийн захирал",
            cls.LECTOR: "Лектор",
            cls.LECTURER_TRAINER: "Лектор, Сургагч",
            cls.LEGAL_ADVISOR: "Хуулийн зөвлөх",
            cls.LIBRARIAN: "Номын сангийн ажилтан",
            cls.LIFEGUARD_SWIMMING_INSTRUCTOR: "Аврагч, Усны спортын зааварлагч",
            cls.LIGHTING_TECHNICIAN: "Гэрлийн техникч",
            cls.LIVESTOCK_SPECIALIST: "Мал аж ахуйн мэргэжилтэн",
            cls.LOAN_SPECIALIST: "Зээлийн мэргэжилтэн",
            cls.LOGISTICS_CLERK: "Логистикийн ажилтан",
            cls.LOGISTICS_CONTROLLER: "Логистикийн хянагч",
            cls.LOGISTICS_DIRECTOR: "Логистикийн захирал",
            cls.LOGISTICS_MANAGER: "Логистикийн менежер",
            cls.LORRY_DRIVER: "Ачааны машины жолооч",
            cls.LOSS_ADJUSTER: "Алдагдлын үнэлгээч",
            cls.LUMBERJACK: "Модчин",
            cls.MACHINE_FITTER: "Машины угсрагч",
            cls.MACHINE_OPERATOR: "Машины оператор",
            cls.MACHINE_OPERATOR_MACHINIST: "Машины оператор, Машинист",
            cls.MACHINE_SETTER: "Машины тохируулагч",
            cls.MAINENTENANCE_WORKER: "Засвар үйлчилгээний ажилтан",
            cls.MAINTENANCE_ENGINEER: "Засвар үйлчилгээний инженер",
            cls.MAINTENANCE_SUPERVISOR: "Засвар үйлчилгээний ахлагч",
            cls.MAINTENANCE_WORKER: "Засвар үйлчилгээний ажилтан",
            cls.MAKE_UP_ARTIST_WIGMAKER: "Гримчин, Үсний дизайнер",
            cls.MANAGING_DIRECTOR: "Гүйцэтгэх захирал",
            cls.MANAGING_EDITOR: "Менежер редактор",
            cls.MARITIME_TRANSPORT_ORGANISER: "Далайн тээврийн зохион байгуулагч",
            cls.MARKETING_ANALYST: "Маркетингийн шинжээч",
            cls.MARKETING_DIRECTOR: "Маркетингийн захирал",
            cls.MARKETING_MANAGER: "Маркетингийн менежер",
            cls.MARKETING_OFFICER: "Маркетингийн ажилтан",
            cls.MARKETING_SPECIALIST: "Маркетингийн мэргэжилтэн",
            cls.MARKETING_ASSISTANT: "Маркетингийн туслах",
            cls.MASTER_IN_VOCATIONAL_EDUCATION: "Мэргэжлийн боловсролын мастер",
            cls.MASSEUR: "Массажист",
            cls.MECHANICAL_DESIGN_ENGINEER_AUTOMATION: "Механик зураг төслийн инженер - Автоматжуулалт",
            cls.MECHANICAL_ENGINEER: "Механик инженер",
            cls.MECHANIZATION_MANAGER: "Механикжуулалтын менежер",
            cls.MEDIA_BUYER: "Медиа худалдан авагч",
            cls.MEDIA_PLANNER: "Медиа төлөвлөгч",
            cls.MEDICAL_ADVISOR: "Анагаах ухааны зөвлөх",
            cls.MEDICAL_INSTITUTION_MANAGER: "Эмнэлгийн байгууллагын менежер",
            cls.MEDICAL_LABORATORY_TECHNICIAN: "Анагаах ухааны лабораторийн техникч",
            cls.MEDICAL_ORDERLY: "Эмнэлгийн санитар",
            cls.MEDICAL_RECORDS_CLERK: "Эмнэлгийн бүртгэлийн ажилтан",
            cls.MEDICAL_ASSISTANT: "Эмнэлгийн туслах",
            cls.MEDICAL_GRADUATE: "Анагаахын төгсөгч",
            cls.MEDICAL_PHARMACEUTICAL_SALES_REPRESENTATIVE: "Анагаах/Эмийн борлуулалтын төлөөлөгч",
            cls.MECHATRONICS_TECHNICIAN: "Мехатроникийн техникч",
            cls.METALLURGIST: "Металлургич",
            cls.METALLURGY_ENGINEER: "Металлургийн инженер",
            cls.METALWORKER: "Металлчин",
            cls.METEOROLOGIST: "Цаг уурч",
            cls.METROLOGIST: "Метрологич",
            cls.MICROBIOLOGIST: "Микробиологич",
            cls.MICROCONTROLLER_PROGRAMMER: "Микроконтроллерийн программист",
            cls.MIDWIFE: "Акушер",
            cls.MILKER: "Сааль саагч",
            cls.MILLING_MACHINE_OPERATOR: "Фрезийн машины оператор",
            cls.MINER: "Уурхайч",
            cls.MINING_ENGINEER: "Уул уурхайн инженер",
            cls.MINING_MANAGER: "Уул уурхайн менежер",
            cls.MINING_TECHNICIAN: "Уул уурхайн техникч",
            cls.MOBILE_NETWORK_DEVELOPMENT_SPECIALIST: "Гар утасны сүлжээ хөгжүүлэлтийн мэргэжилтэн",
            cls.MODEL: "Загварчин",
            cls.MORTGAGE_SPECIALIST: "Ипотекийн мэргэжилтэн",
            cls.MUSIC_AND_ART_SCHOOL_TEACHER: "Хөгжим, Урлагийн сургуулийн багш",
            cls.NANNY: "Хүүхэд харагч",
            cls.NAVAL_OFFICER: "Тэнгисийн офицер",
            cls.NETWORK_MODELLING_SPECIALIST: "Сүлжээний загварчлалын мэргэжилтэн",
            cls.NETWORK_STRATEGY_SPECIALIST: "Сүлжээний стратегийн мэргэжилтэн",
            cls.NETWORK_AND_SERVICE_OPERATION_SPECIALIST: "Сүлжээ ба үйлчилгээний үйл ажиллагааны мэргэжилтэн",
            cls.NOTARY: "Нотариат",
            cls.NOTARY_ASSOCIATE: "Нотариатын туслах",
            cls.NURSE: "Сувилагч",
            cls.NURSERY_SCHOOL_TEACHER_ASSISTANT: "Цэцэрлэгийн багшийн туслах",
            cls.NUTRITION_ASSISTANT: "Хоол тэжээлийн туслах",
            cls.OSS_BSS_SPECIALIST: "OSS/BSS мэргэжилтэн",
            cls.OBJECTIVE_C_PROGRAMMER: "Objective-C программист",
            cls.OCCUPATIONAL_PSYCHOLOGIST: "Хөдөлмөрийн сэтгэл зүйч",
            cls.OCCUPATIONAL_HEALTH_NURSE: "Хөдөлмөрийн эрүүл мэндийн сувилагч",
            cls.OFFICE_MANAGER: "Оффисын менежер",
            cls.OFFICIAL: "Албан тушаалтан",
            cls.ONLINE_SHOP_ADMINISTRATOR: "Онлайн дэлгүүрийн администратор",
            cls.OPERATIONS_MANAGER: "Үйл ажиллагааны менежер",
            cls.OPERATIONS_SUPERVISOR: "Үйл ажиллагааны ахлагч",
            cls.OPTOMETRIST: "Оптометрист",
            cls.ORACLE_PROGRAMMER: "Oracle программист",
            cls.ORGANIZER: "Зохион байгуулагч",
            cls.ORTHOPEDIC_TECHNICIAN: "Ортопедийн техникч",
            cls.PHP_PROGRAMMER: "PHP программист",
            cls.PLC_PROGRAMMER: "PLC программист",
            cls.PPC_SPECIALIST: "PPC мэргэжилтэн",
            cls.PR_MANAGER: "PR менежер",
            cls.PC_TECHNICIAN: "Компьютерийн техникч",
            cls.PACKER: "Савлагч",
            cls.PAINTER: "Будагч",
            cls.PARALEGAL_LAW_STUDENT: "Хуулийн туслах - хуулийн оюутан",
            cls.PASTRY_CHEF_CONFECTIONER: "Бялуучин, Чихэрлэг хоолны тогооч",
            cls.PAYROLL_CLERK: "Цалингийн ажилтан",
            cls.PEDAGOGUE: "Багш, Сурган хүмүүжүүлэгч",
            cls.PEDICURIST_MANICURIST_NAIL_TECHNICIAN: "Педикюрист, Маникюрист, Хумсны техникч",
            cls.PERL_PROGRAMMER: "Perl программист",
            cls.PERSONAL_BANKER: "Хувийн банкир",
            cls.PERSONNEL_MANAGER: "Персоналийн менежер",
            cls.PETROL_STATION_ATTENDANT: "Шатахуун түгээгч",
            cls.PETROLEUM_ENGINEER: "Газрын тосны инженер",
            cls.PHARMACEUTICAL_LABORATORY_TECHNICIAN: "Эмийн лабораторийн техникч",
            cls.PHARMACEUTICAL_PRODUCTS_MANAGER: "Эмийн бүтээгдэхүүний менежер",
            cls.PHARMACIST: "Эм зүйч",
            cls.PHARMACIST_ASSISTANT: "Эм зүйчийн туслах",
            cls.PHOTO_EDITOR: "Фото редактор",
            cls.PHOTOGRAPHER: "Гэрэл зурагчин",
            cls.PHYSIOTHERAPIST: "Физик эмчилгээч",
            cls.PICKER: "Сонгогч",
            cls.PILOT: "Нисгэгч",
            cls.PIPE_FITTER: "Хоолойчин",
            cls.PIZZA_COOK: "Пицца тогооч",
            cls.PLANNING_ASSISTANT: "Төлөвлөлтийн туслах",
            cls.PLANT_MANAGER: "Үйлдвэрийн менежер",
            cls.PLUMBER: "Сантехникч",
            cls.POLICE_INSPECTOR: "Цагдаагийн байцаагч",
            cls.POLICE_OFFICER: "Цагдаа",
            cls.POSTAL_DELIVERY_WORKER: "Шуудангийн хүргэлтийн ажилтан",
            cls.POSTAL_WORKER: "Шуудангийн ажилтан",
            cls.POSTMASTER: "Шуудангийн дарга",
            cls.POWER_ENGINEER: "Эрчим хүчний инженер",
            cls.POWER_GENERATING_MACHINERY_OPERATOR: "Эрчим хүч үйлдвэрлэх машины оператор",
            cls.PRE_SCHOOL_SCHOOL_KINDERGARDER_NURSE: "Сургуулийн өмнөх боловсролын/Цэцэрлэгийн сувилагч",
            cls.PRESCHOOL_TEACHER: "Цэцэрлэгийн багш",
            cls.PRIMARY_SCHOOL_TEACHER: "Бага сургуулийн багш",
            cls.PRIEST: "Лам, Санваартан",
            cls.PRINTER: "Хэвлэгч",
            cls.PRINTING_TECHNICIAN: "Хэвлэлийн техникч",
            cls.PRISON_OFFICER: "Шорон хорих газрын ажилтан",
            cls.PRIVATE_BANKER: "Хувийн банкир",
            cls.PROBLEM_MANAGER: "Асуудлын менежер",
            cls.PROCESS_ENGINEER: "Процессын инженер",
            cls.PROCESS_MANAGER: "Процессын менежер",
            cls.PROCUREMENT_SPECIALIST: "Худалдан авалтын мэргэжилтэн",
            cls.PRODUCER: "Продюсер",
            cls.PRODUCT_DEVELOPMENT_SPECIALIST: "Бүтээгдэхүүн хөгжүүлэлтийн мэргэжилтэн",
            cls.PRODUCT_MANAGER_SPECIALIST: "Бүтээгдэхүүний менежер - Мэргэжилтэн",
            cls.PRODUCT_MARKETING_MANAGER: "Бүтээгдэхүүний маркетингийн менежер",
            cls.PRODUCT_OWNER: "Бүтээгдэхүүний эзэн",
            cls.PRODUCTION_DIRECTOR: "Үйлдвэрлэлийн захирал",
            cls.PRODUCTION_MANAGER: "Үйлдвэрлэлийн менежер",
            cls.PRODUCTION_PLANNER: "Үйлдвэрлэлийн төлөвлөгч",
            cls.PRODUCTION_STANDARD_SETTER: "Үйлдвэрлэлийн стандарт тогтоогч",
            cls.PRODUCTION_SUPERVISOR: "Үйлдвэрлэлийн ахлагч",
            cls.PROFESSOR: "Профессор",
            cls.PROGRAMMER: "Программист",
            cls.PROJECT_ASSISTANT: "Төслийн туслах",
            cls.PROJECT_COORDINATOR: "Төслийн зохицуулагч",
            cls.PROJECT_MANAGER: "Төслийн менежер",
            cls.PROJECT_PLANNER: "Төслийн төлөвлөгч",
            cls.PROMOTIONAL_ASSISTANT: "Сурталчилгааны туслах",
            cls.PROOFREADER: "Эх засагч",
            cls.PROPERTY_MANAGER: "Өмчийн менежер",
            cls.PROSECUTOR: "Прокурор",
            cls.PSYCHOLOGIST: "Сэтгэл зүйч",
            cls.PUBLIC_HEALTH_ADMINISTRATOR: "Нийгмийн эрүүл мэндийн администратор",
            cls.PUBLISHING_HOUSE_DIRECTOR: "Хэвлэлийн газрын захирал",
            cls.PURCHASING_MANAGER: "Худалдан авалтын менежер",
            cls.PYTHON_PROGRAMMER: "Python программист",
            cls.QUALITY_CONTROL_ISO_MANAGER: "Чанарын хяналт/ISO менежер",
            cls.QUALITY_ENGINEER: "Чанарын инженер",
            cls.QUALITY_INSPECTOR: "Чанарын байцаагч",
            cls.QUALITY_MANAGER: "Чанарын менежер",
            cls.QUALITY_PLANNER: "Чанарын төлөвлөгч",
            cls.QUALIFIED_MECHANICAL_ENGINEER: "Мэргэшсэн механик инженер",
            cls.QUANTITY_SURVEYOR: "Тооцооны инженер",
            cls.R_PROGRAMMER: "R программист",
            cls.RADIO_NETWORK_OPTIMIZATION_SPECIALIST: "Радио сүлжээний оновчлолын мэргэжилтэн",
            cls.RADIO_NETWORK_PLANNING_SPECIALIST: "Радио сүлжээний төлөвлөлтийн мэргэжилтэн",
            cls.RADIO_PRESENTER_AND_ANNOUNCER: "Радиогийн нэвтрүүлэгч",
            cls.RADIOGRAPHER: "Рентген зурагч",
            cls.RADIOLOGY_ASSISTANT: "Радиологийн туслах",
            cls.RAIL_TRANSPORT_CONTROLLER_SHUNTER_SIGNALIST: "Төмөр замын хяналтын ажилтан (шунтер, сигналист)",
            cls.REAL_ESTATE_APPRAISER: "Үл хөдлөх хөрөнгийн үнэлгээч",
            cls.REAL_ESTATE_MAINTENANCE: "Үл хөдлөх хөрөнгийн засвар үйлчилгээ",
            cls.RECEPTIONIST: "Хүлээн авалтын ажилтан",
            cls.RECEPTIONIST_I: "Хүлээн авалтын ажилтан I",
            cls.RECRUITER: "Элсэлтийн ажилтан",
            cls.REFRIGERATION_MECHANIC: "Хөргөлтийн механик",
            cls.REGIONAL_AREA_MANAGER: "Бүсийн менежер",
            cls.REGIONAL_MANAGER: "Бүсийн менежер",
            cls.REGISTRY_ADMINISTRATION_OFFICER: "Бүртгэлийн захиргааны ажилтан",
            cls.REGULATORY_AFFAIRS_MANAGER: "Зохицуулалтын асуудлын менежер",
            cls.REGULATORY_AFFAIRS_SPECIALIST: "Зохицуулалтын асуудлын мэргэжилтэн",
            cls.REINSURANCE_SPECIALIST: "Дахин даатгалын мэргэжилтэн",
            cls.RELATIONSHIP_MANAGER: "Харилцааны менежер",
            cls.REPORTER: "Сурвалжлагч",
            cls.REPORTING_SPECIALIST: "Тайлангийн мэргэжилтэн",
            cls.REPAIRER: "Засварч",
            cls.RESEARCH_PHYSICIAN: "Судалгааны эмч",
            cls.RESEARCH_WORKER_SCIENTIFIC_WORKER: "Судалгааны ажилтан, Шинжлэх ухааны ажилтан",
            cls.RESTAURANT_MANAGER: "Ресторанны менежер",
            cls.RESTAURANT_WORKER: "Ресторанны ажилтан",
            cls.RESTORER_CONSERVATOR: "Сэргээн засварлагч",
            cls.RETAIL_STORE_MANAGER: "Жижиглэн худалдааны дэлгүүрийн менежер",
            cls.RETURNS_DEPARTMENT_MANAGER: "Буцаалтын хэлтсийн менежер",
            cls.RISK_MANAGER: "Рискийн менежер",
            cls.RISK_SPECIALIST: "Рискийн мэргэжилтэн",
            cls.ROAMING_SPECIALIST: "Роамингийн мэргэжилтэн",
            cls.ROOFER: "Дээврийн ажилчин",
            cls.RUBY_DEVELOPER_PROGRAMMER: "Ruby хөгжүүлэгч/программист",
            cls.SAP_SPECIALIST: "SAP мэргэжилтэн",
            cls.SEO_ANALYST: "SEO шинжээч",
            cls.SAFETY_SPECIALIST: "Аюулгүй байдлын мэргэжилтэн",
            cls.SAILOR: "Далайч",
            cls.SALES_CONSULTANT: "Борлуулалтын зөвлөх",
            cls.SALES_DIRECTOR: "Борлуулалтын захирал",
            cls.SALES_ENGINEER: "Борлуулалтын инженер",
            cls.SALES_MANAGER: "Борлуулалтын менежер",
            cls.SALES_OBJECT_MANAGER: "Борлуулалтын объектын менежер",
            cls.SALES_OFFICE_MANAGER: "Борлуулалтын оффисын менежер",
            cls.SALES_OFFICER: "Борлуулалтын ажилтан",
            cls.SALES_REPRESENTATIVE: "Борлуулалтын төлөөлөгч",
            cls.SALES_COORDINATOR: "Борлуулалтын зохицуулагч",
            cls.SAW_FILER: "Хөрөө засагч",
            cls.SCAFFOLDER: "Тулгуур барилгач",
            cls.SCHOOL_CANTEEN_MANAGER: "Сургуулийн гуанзны менежер",
            cls.SCHOOL_CARETAKER: "Сургуулийн харуул хамгаалагч",
            cls.SCHOOL_PRINCIPAL: "Сургуулийн захирал",
            cls.SCRUM_MASTER: "Scrum Мастер",
            cls.SEAMSTRESS: "Оёдолчин",
            cls.SECONDARY_SCHOOL_TEACHER: "Дунд сургуулийн багш",
            cls.SECRETARY: "Нарийн бичгийн дарга",
            cls.SECRETARY_OF_HEALTH_DEPARTMENT: "Эрүүл мэндийн хэлтсийн нарийн бичгийн дарга",
            cls.SECURITY_GUARD: "Харуул хамгаалагч",
            cls.SECURITY_SERVICE_DIRECTOR: "Хамгаалалтын үйлчилгээний захирал",
            cls.SECURITY_SERVICE_MANAGER: "Хамгаалалтын үйлчилгээний менежер",
            cls.SECURITY_SERVICE_TECHNICIAN: "Хамгаалалтын үйлчилгээний техникч",
            cls.SELLER_CASHIER: "Худалдагч / Кассир",
            cls.SELLER_OF_BANK_SERVICES_LOAN_OFFICER: "Банкны үйлчилгээний худалдагч, Зээлийн ажилтан",
            cls.SENIOR_ACCOUNTANT: "Ахлах нягтлан бодогч",
            cls.SENIOR_ASSOCIATE: "Ахлах нэгдэл",
            cls.SENIOR_GRAPHIC_DESIGNER: "Ахлах график дизайнер",
            cls.SENIOR_PROJECT_MANAGER: "Ахлах төслийн менежер",
            cls.SENIOR_SALES_REPRESENTATIVE: "Ахлах борлуулалтын төлөөлөгч",
            cls.SENIOR_STATISTICIAN: "Ахлах статистикч",
            cls.SERVICE_ENGINEER: "Үйлчилгээний инженер",
            cls.SERVICE_TECHNICIAN: "Үйлчилгээний техникч",
            cls.SHELF_STACKER_MERCHANDISER: "Тавиур дүүргэгч/Мерчандайзер",
            cls.SHIFT_MANAGER: "Ээлжийн менежер",
            cls.SHOP_ASSISTANT: "Дэлгүүрийн туслах",
            cls.SHOP_WINDOW_DECORATOR: "Дэлгүүрийн цонхны чимэглэгч",
            cls.SMITH: "Дархан",
            cls.SOCIAL_COUNSELOR: "Нийгмийн зөвлөгч",
            cls.SOCIAL_MEDIA_SPECIALIST: "Нийгмийн сүлжээний мэргэжилтэн",
            cls.SOCIAL_REHABILITATION_SPECIALIST: "Нийгмийн нөхөн сэргээлтийн мэргэжилтэн",
            cls.SOFTWARE_ENGINEER: "Програм хангамжийн инженер",
            cls.SOFTWARE_CONSULTANT: "Програм хангамжийн зөвлөх",
            cls.SOLDIER: "Цэрэг",
            cls.SOLICITOR_BARRISTER: "Өмгөөлөгч",
            cls.SOMMELIER: "Сомелье",
            cls.SOUND_ENGINEER: "Дуу авианы инженер",
            cls.SPA_THERAPIST: "Спа эмчилгээч",
            cls.SPATIAL_PLANNER: "Орон зайн төлөвлөгч",
            cls.SPECIAL_NEEDS_TEACHER: "Тусгай хэрэгцээт боловсролын багш",
            cls.SPECIALIST_ADVISOR: "Мэргэжлийн зөвлөх",
            cls.SPECIALIST_OFFICIAL: "Мэргэжлийн албан тушаалтан",
            cls.SPEECH_THERAPIST: "Логопед",
            cls.SPORTS_COACH: "Спортын дасгалжуулагч",
            cls.SPORTS_COORDINATOR: "Спортын зохицуулагч",
            cls.STAGEHAND: "Тайзны ажилтан",
            cls.STATE_ADVISOR: "Улсын зөвлөх",
            cls.STOCK_BROKER: "Хөрөнгийн брокер",
            cls.STOKER_BOILER_ATTENDANT: "Зуухч",
            cls.STONEMASON: "Чулуучин",
            cls.STORE_DEPARTMENT_MANAGER: "Агуулахын хэлтсийн менежер",
            cls.STOREKEEPER: "Агуулахын ажилтан",
            cls.STRUCTURAL_ENGINEER: "Байгууламжийн инженер",
            cls.SUPERINTENDENT: "Ерөнхий хянагч",
            cls.SUPPLY_CHAIN_SPECIALIST: "Нийлүүлэлтийн гинжийн мэргэжилтэн",
            cls.SUPPLY_TECHNICIAN: "Нийлүүлэлтийн техникч",
            cls.SURVEY_INTERVIEWER: "Судалгааны ярилцлагч",
            cls.SWITCHING_NETWORK_DEVELOPMENT_SPECIALIST: "Шилжүүлэлтийн сүлжээ хөгжүүлэлтийн мэргэжилтэн",
            cls.SYSTEMS_ADMINISTRATOR: "Системийн администратор",
            cls.SYSTEMS_ENGINEER: "Системийн инженер",
            cls.TV_PRESENTER: "ТВ нэвтрүүлэгч",
            cls.TV_FILM_PRODUCTION_ASSISTANT: "ТВ/Киноны үйлдвэрлэлийн туслах",
            cls.TAILOR: "Оёдолчин",
            cls.TAX_ADVISOR: "Татварын зөвлөх",
            cls.TAXI_DRIVER: "Таксины жолооч",
            cls.TEACHER: "Багш",
            cls.TEAM_LEADER: "Багийн ахлагч",
            cls.TECHNICAL_DIRECTOR: "Техникийн захирал",
            cls.TECHNICAL_MANAGER: "Техникийн менежер",
            cls.TECHNICAL_STAFF: "Техникийн ажилтан",
            cls.TECHNICAL_SUPPORT_SPECIALIST: "Техникийн дэмжлэгийн мэргэжилтэн",
            cls.TECHNICAL_WRITER: "Техникийн бичгийн ажилтан",
            cls.TECHNICAL_PRODUCT_ENGINEER: "Техникийн бүтээгдэхүүний инженер",
            cls.TELECOMMUNICATION_SPECIALIST: "Харилцаа холбооны мэргэжилтэн",
            cls.TELECOMMUNICATION_NETWORK_INSTALLER: "Харилцаа холбооны сүлжээ угсрагч",
            cls.TELECOMMUNICATIONS_NETWORK_DESIGNER: "Харилцаа холбооны сүлжээний дизайнер",
            cls.TELECOMMUNICATIONS_PRODUCT_DEVELOPMENT_SPECIALIST: "Харилцаа холбооны бүтээгдэхүүн хөгжүүлэлтийн мэргэжилтэн",
            cls.TELECOMMUNICATIONS_SERVICE_DEVELOPMENT_SPECIALIST: "Харилцаа холбооны үйлчилгээ хөгжүүлэлтийн мэргэжилтэн",
            cls.TELEMARKETER: "Утсаар маркетинг хийгч",
            cls.TERMINAL_OPERATOR: "Терминалийн оператор",
            cls.TESTING_MANAGER: "Туршилтын менежер",
            cls.TECHNICIAN: "Техникч",
            cls.TECHNOLOGIST: "Технологич",
            cls.TILE_MAN: "Хавтанч",
            cls.TIMBER_ENGINEER: "Модон материалын инженер",
            cls.TOOLMAKER: "Хэрэгсэл үйлдвэрлэгч",
            cls.TRAFFIC_CONTROLLER: "Замын хөдөлгөөний хяналтын ажилтан",
            cls.TRAFFIC_ENGINEER: "Замын хөдөлгөөний инженер",
            cls.TRAIN_CONDUCTOR: "Галт тэргний кондуктор",
            cls.TRAIN_DISPATCHER: "Галт тэргний диспетчер",
            cls.TRAINEE_BAILIFF: "Дадлагажигч биелэлтийн ажилтан",
            cls.TRAM_DRIVER: "Трамвайн жолооч",
            cls.TRANSMISSION_NETW_ANALYSIS_DEVELOPMENT_SPECIALIST: "Дамжуулалтын сүлжээний шинжилгээ ба хөгжүүлэлтийн мэргэжилтэн",
            cls.TRANSPORT_MANAGER: "Тээврийн менежер",
            cls.TRAVEL_GUIDE: "Аялалын хөтөч",
            cls.TROLLEYBUS_DRIVER: "Троллейбусны жолооч",
            cls.TUTOR: "Хувийн багш",
            cls.TYRE_FITTER: "Дугуй угсрагч",
            cls.UX_DESIGNER: "UX дизайнер",
            cls.UNIVERSITY_TEACHER: "Их сургуулийн багш",
            cls.UNIVERSITY_TEACHING_ASSISTANT: "Их сургуулийн багшийн туслах",
            cls.UPHOLSTERER: "Эдлэлчин",
            cls.USER_EXPERIENCE_EXPERT: "Хэрэглэгчийн туршлагын мэргэжилтэн",
            cls.VAT_SPECIALIST: "НӨАТ-ийн мэргэжилтэн",
            cls.VFX_ARTIST: "VFX уран бүтээлч",
            cls.VARNISHER: "Лак түрхэгч",
            cls.VEHICLE_BODY_REPAIRER: "Тээврийн хэрэгслийн бие засварч",
            cls.VETERINARIAN: "Малын эмч",
            cls.VETERINARY_TECHNICIAN: "Малын эмнэлгийн техникч",
            cls.VISUAL_MERCHANDISER: "Визуал мерчандайзер",
            cls.WAITER: "Зөөгч",
            cls.WAITER_ROOM_SERVICE: "Зөөгч - Өрөөний үйлчилгээ",
            cls.WARD_DOMESTIC: "Тасгийн гэрийн ажилтан",
            cls.WARDROBE_ASSISTANT: "Хувцасны туслах",
            cls.WAREHOUSE_MANAGER: "Агуулахын менежер",
            cls.WAREHOUSEMAN: "Агуулахч",
            cls.WATER_MANAGEMENT_ENGINEER: "Усны менежментийн инженер",
            cls.WATER_MANAGEMENT_TECHNICIAN: "Усны менежментийн техникч",
            cls.WEB_DESIGNER: "Веб дизайнер",
            cls.WEBMASTER: "Вебмастер",
            cls.WELDER: "Гагнуурч",
            cls.WINDOW_DRESSER_DECORATOR: "Цонхны чимэглэгч",
            cls.WOODWORKING_TECHNICIAN: "Модон эдлэлийн техникч",
            cls.YOUTH_WORKER: "Залуучуудын ажилтан",
            cls.IOS_DEVELOPER: "iOS хөгжүүлэгч",
            cls.OTHER: "Бусад",
        }

    @property
    def mongolian_name(self) -> str:
        return self._mongolian_names().get(self, self.value)
