from __future__ import annotations

import json
import re
import asyncio
from enum import Enum
from typing import Any, List, Optional, cast

from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent



class UnifiedJobLevelCategory(str, Enum):
    """Unified job level categorization combining holding and techpack approaches."""
    EXECUTIVE_MANAGEMENT = "Захирал"  # CEO, Deputy Directors
    SENIOR_MANAGEMENT = "Дарга/Нэгжийн удирдлага"  # Directors, Senior Managers
    MIDDLE_MANAGEMENT = "Ахлах менежер"  # Senior Managers, Department Heads
    MANAGER = "Менежер"  # Managers, Team Leads
    SPECIALIST_SENIOR = "Ахлах мэргэжилтэн"  # Senior Specialists
    SPECIALIST = "Мэргэжилтэн"  # Specialists
    STAFF = "Ажилтан"  # General Staff

    @property
    def description(self) -> str:
        descriptions = {
            UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT: 
                "Top executive leadership (CEO, Deputy Directors, C-suite). Job grades 10-11. "
                "Responsible for overall organizational strategy, board-level decisions, and company-wide management. "
                "Requires 15+ years experience with proven executive track record.",
            
            UnifiedJobLevelCategory.SENIOR_MANAGEMENT: 
                "Senior leadership roles (Directors, Functional Heads). Job grades 8-9. "
                "Manages multiple departments or major functions, sets strategic direction within domain, "
                "develops senior managers. Requires 10-15 years experience.",
            
            UnifiedJobLevelCategory.MIDDLE_MANAGEMENT:
                "Senior management (Senior Managers, Department Heads). Job grades 7-8. "
                "Manages multiple teams/departments, tactical execution, budget oversight. "
                "Requires 7-12 years experience with leadership capabilities.",

            UnifiedJobLevelCategory.MANAGER:
                "Mid-level management (Managers, Team Leads, Supervisors). Job grades 6-7. "
                "Manages teams, day-to-day execution, people management. "
                "Requires 4-8 years experience with leadership capabilities.",

            UnifiedJobLevelCategory.SPECIALIST_SENIOR:
                "Senior professional specialists with advanced expertise. Job grades 5-6. "
                "Subject matter experts, complex problem solving, mentoring, project leadership. "
                "Requires 6-10 years specialized experience.",
            
            UnifiedJobLevelCategory.SPECIALIST: 
                "Professional specialists with domain expertise. Job grades 3-4. "
                "Independent professional work, specialized skills, moderate complexity tasks. "
                "Requires 2-6 years experience with university degree.",
            
            UnifiedJobLevelCategory.STAFF: 
                "Entry to junior level staff positions. Job grades 1-2. "
                "Operational tasks, foundational work, learning and executing procedures. "
                "Requires 0-3 years experience."
        }
        return descriptions.get(self, self.value)

    @property
    def salary_multiplier(self) -> float:
        """Salary multiplier relative to base specialist level."""
        multipliers = {
            UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT: 3.5,
            UnifiedJobLevelCategory.SENIOR_MANAGEMENT: 2.5,
            UnifiedJobLevelCategory.MIDDLE_MANAGEMENT: 2.0,
            UnifiedJobLevelCategory.MANAGER: 1.8,
            UnifiedJobLevelCategory.SPECIALIST_SENIOR: 1.5,
            UnifiedJobLevelCategory.SPECIALIST: 1.0,
            UnifiedJobLevelCategory.STAFF: 0.6
        }
        return multipliers.get(self, 1.0)

class ExperienceLevel(str, Enum):
    """Experience level categories. as 0-36month, 37-84month, 85+ month"""
    ENTRY = "0-36"
    INTERMEDIATE = "37-84"
    EXPERT = "85+"

    @property
    def years_range(self) -> tuple[int, int]:
        ranges = {
            ExperienceLevel.ENTRY: (0, 36),
            ExperienceLevel.INTERMEDIATE: (37, 84),
            ExperienceLevel.EXPERT: (85, 1000)
        }
        return ranges.get(self, (0, 2))

    @property
    def salary_multiplier(self) -> float:
        multipliers = {
            ExperienceLevel.ENTRY: 0.7,
            ExperienceLevel.INTERMEDIATE: 1.0,
            ExperienceLevel.EXPERT: 1.6
        }
        return multipliers.get(self, 1.0)

class EducationLevel(str, Enum):
    """Education level categories."""
    HIGH_SCHOOL = "Бүрэн дунд"
    VOCATIONAL = "Мэргэжлийн"
    BACHELOR = "Бакалавр"
    MASTER = "Магистр"
    DOCTORATE = "Доктор"

    @property
    def salary_multiplier(self) -> float:
        multipliers = {
            EducationLevel.HIGH_SCHOOL: 0.8,
            EducationLevel.VOCATIONAL: 0.9,
            EducationLevel.BACHELOR: 1.0,
            EducationLevel.MASTER: 1.2,
            EducationLevel.DOCTORATE: 1.4
        }
        return multipliers.get(self, 1.0)

class JobRequirement(BaseModel):
    """Requirements for a job position."""
    name: str = Field(..., description="Requirement category name (e.g., Education, Experience, Skills). Must be in Mongolian.")
    details: str = Field(..., description="Specific requirement details including qualifications, years of experience, certifications, etc. Must be in Mongolian.")
    importance: str = Field(default="Чухал", description="Importance level: 'Маш чухал' (Critical), 'Чухал' (Important), 'Хүсэлтэй' (Desired)")

class JobBenefit(BaseModel):
    """Benefits and bonuses for a job position."""
    name: str = Field(..., description="Name of the benefit or bonus (e.g., Performance Bonus, Health Insurance). Must be in Mongolian.")
    description: str = Field(..., description="Details about the benefit including conditions, amounts, frequency. Must be in Mongolian.")
    monetary_value: Optional[int] = Field(None, description="Estimated monthly monetary value in MNT if applicable.")

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

    @property
    def description(self) -> str:
        descriptions = {
            JobFunctionCategory.STORAGE: "Warehouse and storage operations including inventory management, logistics coordination, and materials handling.",
            JobFunctionCategory.AUDIT_RISK_COMPLIANCE: "Internal and external audit functions, enterprise risk management, and regulatory compliance activities.",
            JobFunctionCategory.SALES: "Direct sales roles focused on revenue generation, client acquisition, and account management across various industries.",
            JobFunctionCategory.BUSINESS_DEVELOPMENT: "Strategic growth initiatives including partnership development, market expansion, and new business opportunities.",
            JobFunctionCategory.EXECUTIVE_MANAGEMENT: "C-suite and senior leadership positions responsible for overall organizational strategy and direction.",
            JobFunctionCategory.ADMINISTRATION: "Administrative support and office management functions ensuring smooth operational workflows.",
            JobFunctionCategory.ENGINEERING_TECHNICAL: "Technical and engineering roles involving design, maintenance, and operation of equipment and systems.",
            JobFunctionCategory.CONTENT_DESIGN: "Creative roles in content creation, graphic design, multimedia production, and visual communications.",
            JobFunctionCategory.MARKETING_PR: "Marketing strategy, brand management, public relations, and communications activities.",
            JobFunctionCategory.IT_TELECOM: "Information technology and telecommunications roles including software development, infrastructure, and systems administration.",
            JobFunctionCategory.FINANCE_ACCOUNTING: "Financial planning, accounting, investment management, and related financial services.",
            JobFunctionCategory.PROJECT_ALL: "Project management and coordination roles across all industries and project types.",
            JobFunctionCategory.DISTRIBUTION_TRANSPORT: "Transportation, logistics, and distribution activities for goods and materials.",
            JobFunctionCategory.MANUFACTURING: "Production and manufacturing operations including assembly, quality control, and process management.",
            JobFunctionCategory.SERVICE_CLEANING: "Service industry roles including cleaning, maintenance, and facility management.",
            JobFunctionCategory.HSE_BO: "Health, safety, environment, and business operations management ensuring workplace safety and regulatory compliance.",
            JobFunctionCategory.CUSTOMER_SERVICE: "Customer-facing support roles focused on client satisfaction and issue resolution.",
            JobFunctionCategory.SECURITY: "Security and protection services including physical security, surveillance, and risk mitigation.",
            JobFunctionCategory.PROCUREMENT: "Purchasing, vendor management, and supply chain procurement activities.",
            JobFunctionCategory.HR: "Human resources functions including recruitment, employee relations, compensation, and organizational development.",
            JobFunctionCategory.LEGAL: "Legal counsel, contract management, and regulatory compliance activities.",
            JobFunctionCategory.HEALTHCARE: "Healthcare and medical services including clinical, administrative, and support roles.",
            JobFunctionCategory.OTHER: "Roles that do not fit into the predefined categories, encompassing a wide range of job functions across various industries."   
        }
        return descriptions.get(self, self.value)

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
    @property
    def description(self) -> str:
        descriptions = {
            JobIndustryCategory.AGRICULTURE_FORESTRY_FISHING_HUNTING: "Agriculture, forestry, fishing, and hunting industry including crop production, animal production, forestry, fishing, and related activities.",
            JobIndustryCategory.MINING_QUARRYING_OIL_GAS_EXTRACTION: "Mining and extraction of minerals, oil, gas, and other natural resources.",
            JobIndustryCategory.MANUFACTURING: "Manufacturing of goods across various sectors including food production, textiles, machinery, and more.",
            JobIndustryCategory.ELECTRICITY_GAS_STEAM_AIR_CONDITIONING_SUPPLY: "Generation and distribution of electricity, gas, steam, and air conditioning supply.",
            JobIndustryCategory.WATER_SEWERAGE_WASTE_MANAGEMENT_REMEDIATION: "Water supply and sewage systems, waste management services, and environmental remediation activities.",
            JobIndustryCategory.CONSTRUCTION: "Construction of buildings, infrastructure projects, and related activities.",
            JobIndustryCategory.WHOLESALE_RETAIL_TRADE_REPAIR_MOTOR_VEHICLES_MOTORCYCLES: "Wholesale and retail trade of motor vehicles and motorcycles including repair services.",
            JobIndustryCategory.TRANSPORTATION_WAREHOUSING: "Transportation of goods and passengers as well as warehousing and storage services.",
            JobIndustryCategory.ACCOMMODATION_FOOD_SERVICES: "Accommodation services such as hotels and food services including restaurants and catering.",
            JobIndustryCategory.INFORMATION_COMMUNICATION: "Information technology services, telecommunications, and related communication services.",
            JobIndustryCategory.FINANCE_INSURANCE: "Financial services including banking, insurance, investment management, and related activities.",
            JobIndustryCategory.REAL_ESTATE_RENTAL_LEASING: "Real estate activities including rental and leasing of properties.",
            JobIndustryCategory.PROFESSIONAL_SCIENTIFIC_TECHNICAL_SERVICES: "Professional services in scientific research, technical consulting, legal advice, accounting, and similar fields.",
            JobIndustryCategory.MANAGEMENT_SUPPORT_WASTE_MANAGEMENT_REMIDIATION_SERVICES: "Management support services including administrative support, waste management services, and remediation services.",
            JobIndustryCategory.PUBLIC_ADMINISTRATION_DEFENSE_SOCIAL_SECURITY: "Public administration including government services, defense activities, social security administration.",
            JobIndustryCategory.EDUCATION: "Educational services including schools, universities, training centers.",
            JobIndustryCategory.HEALTHCARE_SOCIAL_ASSISTANCE: "Healthcare services including hospitals, clinics, social assistance services.",
            JobIndustryCategory.ARTS_ENTERTAINMENT_RECREATION: "Arts, entertainment, and recreation services including performing arts, spectator sports, museums, and amusement parks.",
            JobIndustryCategory.OTHER_SERVICES: "Other services not classified in the above categories including repair and maintenance services, personal services, and similar activities.",
            JobIndustryCategory.HOUSEHOLD_EMPLOYERS: "Household employers including domestic workers, nannies, housekeepers, and similar roles.",
            JobIndustryCategory.INTERNATIONAL_ORGANIZATION_DIPLOMATIC_SERVICES: "International organizations and diplomatic services including roles in embassies, consulates, international agencies, and similar entities.",
            JobIndustryCategory.OTHER: "Other categories not specifically listed." 
        }

        return descriptions.get(self, self.value)


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

    @property
    def mongolian_name(self) -> str:
        names = {
            Category.ADMINISTRATION: "Захиргаа",
            Category.AGRICULTURE_FOOD_INDUSTRY: "Хөдөө аж ахуй, хүнсний үйлдвэр",
            Category.ARTS_CULTURE: "Урлаг & Соёл",
            Category.BANKING: "Банк",
            Category.CAR_INDUSTRY: "Автомашины үйлдвэр",
            Category.CHEMICAL_INDUSTRY: "Химийн үйлдвэр",
            Category.COMMERCE: "Худалдаа",
            Category.CONSTRUCTION_REAL_ESTATE: "Барилга & Үл хөдлөх хөрөнгө",
            Category.CUSTOMER_SUPPORT: "Үйлчлүүлэгчийн тусламж",
            Category.ECONOMY_FINANCE_ACCOUNTANCY: "Эдийн засаг, Санхүү, Нягтлан бодох бүртгэл",
            Category.EDUCATION_SCIENCE_RESEARCH: "Боловсрол, Шинжлэх ухаан & Судалгаа",
            Category.ELECTRICAL_POWER_ENGINEERING: "Цахилгаан & Эрчим хүчний инженерчлэл",
            Category.GENERAL_LABOUR: "Ерөнхий хөдөлмөр",
            Category.HUMAN_RESOURCES: "Хүний нөөц",
            Category.INFORMATION_TECHNOLOGY: "Мэдээллийн технологи",
            Category.INSURANCE: "Даатгал",
            Category.JOURNALISM_PRINTING_ARTS_MEDIA: "Сэтгүүл зүй, Хэвлэх урлаг & Медиа",
            Category.LAW_LEGISLATION: "Хууль & Хууль тогтоомж",
            Category.LEASING: "Лизинг",
            Category.MANAGEMENT: "Менежмент",
            Category.MARKETING_ADVERTISING_PR: "Маркетинг, Сурталчилгаа, PR",
            Category.MECHANICAL_ENGINEERING: "Механик инженерчлэл",
            Category.MEDICINE_SOCIAL_CARE: "Анагаах ухаан & Нийгмийн халамж",
            Category.MINING_METALLURGY: "Уул уурхай, Металлурги",
            Category.PHARMACEUTICAL_INDUSTRY: "Эмийн үйлдвэр",
            Category.PRODUCTION: "Үйлдвэрлэл",
            Category.PUBLIC_ADMINISTRATION_SELF_GOVERNANCE: "Төрийн захиргаа, Өөрөө удирдах ёс",
            Category.QUALITY_MANAGEMENT: "Чанарын менежмент",
            Category.SECURITY_PROTECTION: "Аюулгүй байдал & Хамгаалалт",
            Category.SERVICE_INDUSTRIES: "Үйлчилгээний салбар",
            Category.TECHNOLOGY_DEVELOPMENT: "Технологи, Хөгжүүлэлт",
            Category.TELECOMMUNICATIONS: "Харилцаа холбоо",
            Category.TEXTILE_LEATHER_APPAREL_INDUSTRY: "Нэхмэл, Арьс шир, Хувцасны үйлдвэр",
            Category.TOP_MANAGEMENT: "Дээд удирдлага",
            Category.TOURISM_GASTRONOMY_HOTEL_BUSINESS: "Аялал жуулчлал, Хоол хүнс, Зочид буудлын бизнес",
            Category.TRANSLATING_INTERPRETING: "Орчуулга, Тайлбарлах",
            Category.TRANSPORT_HAULAGE_LOGISTICS: "Тээвэр, Ачаа тээвэр, Логистик",
            Category.WATER_MANAGEMENT_FORESTRY_ENVIRONMENT: "Усны менежмент, Ойн аж ахуй, Байгаль орчин",
            Category.WOOD_PROCESSING_INDUSTRY: "Модон материал боловсруулах үйлдвэр",
        }
        return names.get(self, self.value)


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

    @property
    def mongolian_name(self) -> str:
        names = {
            PositionalCategory.NET_PROGRAMMER: ".NET программист",
            PositionalCategory.ABAP_PROGRAMMER: "ABAP программист",
            PositionalCategory.AI_ENGINEER: "Хиймэл оюун ухааны инженер",
            PositionalCategory.ASP_NET_PROGRAMMER: "ASP.NET программист",
            PositionalCategory.ACCOUNT_DIRECTOR: "Дансны захирал",
            PositionalCategory.ACCOUNT_EXECUTIVE: "Дансны гүйцэтгэх ажилтан",
            PositionalCategory.ACCOUNT_MANAGER: "Дансны менежер",
            PositionalCategory.ACCOUNTANT: "Нягтлан бодогч",
            PositionalCategory.ACCOUNTING_CLERK: "Нягтлан бодох бүртгэлийн ажилтан",
            PositionalCategory.ACCOUNTING_SERVICE_MANAGER: "Нягтлан бодох бүртгэлийн үйлчилгээний менежер",
            PositionalCategory.ACCOMMODATION_MANAGER: "Байрны менежер",
            PositionalCategory.ACTOR: "Жүжигчин",
            PositionalCategory.ACTIVITY_INSTRUCTOR: "Үйл ажиллагааны зааварлагч",
            PositionalCategory.ADMINISTRATIVE_WORKER: "Захиргааны ажилтан",
            PositionalCategory.ADMINISTRATIVE_OFFICER: "Захиргааны офицер",
            PositionalCategory.AGRICULTURAL_ENGINEER_AGRONOMIST: "Хөдөө аж ахуйн инженер, Агрономч",
            PositionalCategory.AGRICULTURAL_EQUIPMENT_OPERATOR: "Хөдөө аж ахуйн тоног төхөөрөмжийн оператор",
            PositionalCategory.AGRICULTURAL_SPECIALIST: "Хөдөө аж ахуйн мэргэжилтэн",
            PositionalCategory.AGRICULTURAL_TECHNICIAN: "Хөдөө аж ахуйн техникч",
            PositionalCategory.AGRICULTURAL_TECHNOLOGIST: "Хөдөө аж ахуйн технологич",
            PositionalCategory.AIR_TRAFFIC_CONTROLLER: "Агаарын хөдөлгөөний хяналтын ажилтан",
            PositionalCategory.AIRCRAFT_TECHNICIAN: "Нисэх онгоцны техникч",
            PositionalCategory.AIRCRAFT_ENGINEER: "Нисэх онгоцны инженер",
            PositionalCategory.AMBULANCE_DRIVER: "Түргэн тусламжийн жолооч",
            PositionalCategory.AMBULANCE_PARAMEDIC: "Түргэн тусламжийн парамедик",
            PositionalCategory.ANESTHETIST: "Мэдээ алдуулагч эмч",
            PositionalCategory.ANIMAL_CARE_WORKER: "Амьтны асаргааны ажилтан",
            PositionalCategory.ANTI_MONEY_LAUNDERING_SPECIALIST: "Мөнгө угаахтай тэмцэх мэргэжилтэн",
            PositionalCategory.ARCHAEOLOGIST: "Археологич",
            PositionalCategory.ARCHITECT: "Архитектор",
            PositionalCategory.ART_DIRECTOR: "Урлагийн захирал",
            PositionalCategory.ARCHIVIST_REGISTRY_ADMINISTRATOR: "Архивч, Бүртгэлийн администратор",
            PositionalCategory.ASSISTANT: "Туслах",
            PositionalCategory.ASSISTANT_COOK: "Тогооч туслах",
            PositionalCategory.ASSISTANT_FINANCIAL_CONTROLLER: "Санхүүгийн хяналтын туслах",
            PositionalCategory.ASSISTANT_TEACHER: "Багшийн туслах",
            PositionalCategory.ASSISTANT_OF_AUDITOR: "Аудиторын туслах",
            PositionalCategory.ASSISTANT_TO_A_TAX_ADVISOR: "Татварын зөвлөхийн туслах",
            PositionalCategory.AU_PAIR: "Ау-пэйр",
            PositionalCategory.AUDITOR: "Аудитор",
            PositionalCategory.AUTO_ELECTRICIAN: "Автомашины цахилгаанч",
            PositionalCategory.AUTO_REPAIR_SHOP_MANAGER: "Автомашины засварын газрын менежер",
            PositionalCategory.AUTOMATION_ENGINEER: "Автоматжуулалтын инженер",
            PositionalCategory.AUTOMATION_PLANNER: "Автоматжуулалтын төлөвлөгч",
            PositionalCategory.AXEMAN: "Сүхчин",
            PositionalCategory.BACK_OFFICE_SPECIALIST: "Арын оффисын мэргэжилтэн",
            PositionalCategory.BAILIFF_ENFORCEMENT_OFFICER: "Шүүхийн биелэлтийн ажилтан",
            PositionalCategory.BAKER: "Талхчин",
            PositionalCategory.BARTENDER: "Бартендер",
            PositionalCategory.BEAUTICIAN: "Гоо сайханч",
            PositionalCategory.BETTING_CLERK: "Бооцооны ажилтан",
            PositionalCategory.BICYCLE_MECHANIC: "Дугуйн механик",
            PositionalCategory.BIDDING_ENGINEER: "Тендерийн инженер",
            PositionalCategory.BILLING_CLERK: "Тооцооны ажилтан",
            PositionalCategory.BIOLOGIST: "Биологич",
            PositionalCategory.BOOKBINDER: "Номын хавтасч",
            PositionalCategory.BOOKMAKER: "Бооцооны компанийн ажилтан",
            PositionalCategory.BOOKING_AGENT: "Захиалгын агент",
            PositionalCategory.BOSUN: "Хөлөг онгоцны ахлагч",
            PositionalCategory.BRANCH_DIRECTOR: "Салбарын захирал",
            PositionalCategory.BRAND_MANAGER: "Брэндийн менежер",
            PositionalCategory.BRICKLAYER: "Тоосгочин",
            PositionalCategory.BUILDING_CONTROL_SURVEYOR: "Барилгын хяналтын хэмжигч",
            PositionalCategory.BUILDING_TECHNICIAN: "Барилгын техникч",
            PositionalCategory.BUS_DRIVER: "Автобусны жолооч",
            PositionalCategory.BUSINESS_ANALYST: "Бизнес шинжээч",
            PositionalCategory.BUSINESS_DEVELOPMENT_MANAGER: "Бизнесийн хөгжлийн менежер",
            PositionalCategory.BUSINESS_GROUP_MANAGER: "Бизнесийн бүлгийн менежер",
            PositionalCategory.BUSINESS_INTELLIGENCE_SPECIALIST: "Бизнесийн тагнуулын мэргэжилтэн",
            PositionalCategory.BUTCHER: "Махчин",
            PositionalCategory.BUYING_AGENT: "Худалдан авалтын агент",
            PositionalCategory.C_PROGRAMMER: "C программист",
            PositionalCategory.CSHARP_PROGRAMMER: "C# программист",
            PositionalCategory.CPP_PROGRAMMER: "C++ программист",
            PositionalCategory.CAD_SPECIALIST: "CAD мэргэжилтэн",
            PositionalCategory.CNC_MACHINE_SETTER: "CNC машины тохируулагч",
            PositionalCategory.CNC_PROGRAMMER: "CNC программист",
            PositionalCategory.CRM_SPECIALIST: "CRM мэргэжилтэн",
            PositionalCategory.CSR_SPECIALIST: "CSR мэргэжилтэн",
            PositionalCategory.CABINET_MAKER: "Тавилгачин",
            PositionalCategory.CABLE_CAR_OPERATOR: "Кабины машины оператор",
            PositionalCategory.CALL_CENTER_SUPERVISOR: "Дуудлагын төвийн ахлагч",
            PositionalCategory.CALL_CENTRE_DIRECTOR: "Дуудлагын төвийн захирал",
            PositionalCategory.CALL_CENTRE_MANAGER: "Дуудлагын төвийн менежер",
            PositionalCategory.CALL_OPERATOR: "Дуудлагын оператор",
            PositionalCategory.CAMERA_OPERATOR: "Камерын оператор",
            PositionalCategory.CAR_DRIVER: "Автомашины жолооч",
            PositionalCategory.CAR_FLEET_MANAGER: "Автопаркын менежер",
            PositionalCategory.CAR_GLASS_FITTER: "Автомашины шилний угсрагч",
            PositionalCategory.CAR_MECHANIC: "Автомашины механик",
            PositionalCategory.CAR_UPHOLSTERER: "Автомашины эдлэлчин",
            PositionalCategory.CAR_WASH_WORKER: "Автомашин угаагч",
            PositionalCategory.CAR_SALESMAN: "Автомашины худалдагч",
            PositionalCategory.CAREER_ADVISOR: "Карьерын зөвлөх",
            PositionalCategory.CAREGIVER: "Асрагч",
            PositionalCategory.CARER_PERSONAL_ASSISTANT: "Асрагч, Хувийн туслах",
            PositionalCategory.CARPENTER: "Мужаан",
            PositionalCategory.CASEWORKER: "Хэргийн ажилтан",
            PositionalCategory.CASHIER: "Кассир",
            PositionalCategory.CATERING_MANAGER: "Хоолны үйлчилгээний менежер",
            PositionalCategory.CHAMBERMAID: "Өрөөний үйлчлэгч",
            PositionalCategory.CHARGE_NURSE: "Ахлах сувилагч",
            PositionalCategory.CHEMICAL_ENGINEER: "Химийн инженер",
            PositionalCategory.CHEMICAL_LAB_TECHNICIAN: "Химийн лабораторийн техникч",
            PositionalCategory.CHEMIST: "Химич",
            PositionalCategory.CHEF: "Ерөнхий тогооч",
            PositionalCategory.CHIEF_ACCOUNTANT: "Ерөнхий нягтлан бодогч",
            PositionalCategory.CHIEF_ACCOUNTANT_DEPUTY: "Ерөнхий нягтлан бодогчийн орлогч",
            PositionalCategory.CHIEF_ADVISOR: "Ерөнхий зөвлөх",
            PositionalCategory.CHIEF_EXECUTIVE_OFFICER: "Гүйцэтгэх захирал",
            PositionalCategory.CHIEF_OFFICIAL: "Ерөнхий албан тушаалтан",
            PositionalCategory.CHIEF_RECEPTIONIST_OFFICER: "Ерөнхий хүлээн авалтын ажилтан",
            PositionalCategory.CHIEF_STATE_ADVISOR: "Улсын ерөнхий зөвлөх",
            PositionalCategory.CHIEF_BOROUGH_CONTROLLER: "Дүүргийн ерөнхий хяналтын ажилтан",
            PositionalCategory.CHOREOGRAPHER: "Хореограф",
            PositionalCategory.CIVIL_ENGINEER: "Иргэний инженер",
            PositionalCategory.CLAIMS_ADMINISTRATOR: "Нэхэмжлэлийн администратор",
            PositionalCategory.CLAIMS_SPECIALIST: "Нэхэмжлэлийн мэргэжилтэн",
            PositionalCategory.CLEANER: "Цэвэрлэгч",
            PositionalCategory.CLEANING_MANAGER: "Цэвэрлэгээний менежер",
            PositionalCategory.CLIENT_OFFICER: "Үйлчлүүлэгчийн ажилтан",
            PositionalCategory.CLINICAL_DATA_MANAGER: "Клиникийн өгөгдлийн менежер",
            PositionalCategory.CLINICAL_PSYCHOLOGIST: "Клиникийн сэтгэл зүйч",
            PositionalCategory.CLINICAL_RESEARCH_ASSOCIATE: "Клиникийн судалгааны нэгдэл",
            PositionalCategory.CLOTHING_TEXTILE_TECHNOLOGIST: "Хувцас/нэхмэлийн технологич",
            PositionalCategory.COACH: "Дасгалжуулагч",
            PositionalCategory.CO_ORDINATOR: "Зохицуулагч",
            PositionalCategory.COBBLER: "Гуталчин",
            PositionalCategory.COLLEGE_LECTOR: "Коллежийн лектор",
            PositionalCategory.COMPLAINTS_DEPARTMENT_CLERK: "Гомдлын хэлтсийн ажилтан",
            PositionalCategory.COMPLIANCE_SPECIALIST: "Дагаж мөрдөх мэргэжилтэн",
            PositionalCategory.COMPENSATION_BENEFIT_SPECIALIST: "Нөхөн олговор ба тэтгэмжийн мэргэжилтэн",
            PositionalCategory.CONCIERGE: "Консьерж",
            PositionalCategory.CONSTRUCTION_MANAGER: "Барилгын менежер",
            PositionalCategory.CONSTRUCTION_PLANT_OPERATOR: "Барилгын тоног төхөөрөмжийн оператор",
            PositionalCategory.CONSTRUCTION_WORKER: "Барилгын ажилтан",
            PositionalCategory.CONSULTANT: "Зөвлөх",
            PositionalCategory.CONTENT_PROVIDER: "Контент нийлүүлэгч",
            PositionalCategory.CONTRACT_ADMINISTRATOR: "Гэрээний администратор",
            PositionalCategory.CONTROLLER: "Хянагч",
            PositionalCategory.COOK: "Тогооч",
            PositionalCategory.COPYWRITER: "Копирайтер",
            PositionalCategory.COST_ACCOUNTANT: "Зардлын нягтлан бодогч",
            PositionalCategory.COUNTER_CLERK: "Лавлагааны ажилтан",
            PositionalCategory.COUNTRY_MANAGER_DIRECTOR: "Улсын менежер/захирал",
            PositionalCategory.COURIER: "Курьер",
            PositionalCategory.CRANE_OPERATOR: "Кран оператор",
            PositionalCategory.CRISIS_WORKER: "Хямралын ажилтан",
            PositionalCategory.CROUPIER: "Крупье",
            PositionalCategory.CULTURAL_OFFICER: "Соёлын ажилтан",
            PositionalCategory.CURATOR: "Куратор",
            PositionalCategory.CUSTOMER_RELATIONSHIP_MANAGER: "Үйлчлүүлэгчтэй харилцах менежер",
            PositionalCategory.CUSTOMER_SUPPORT_SPECIALIST: "Үйлчлүүлэгчийн дэмжлэгийн мэргэжилтэн",
            PositionalCategory.CUSTOMER_SERVICE_ANALYST: "Үйлчлүүлэгчийн үйлчилгээний шинжээч",
            PositionalCategory.CUSTOMS_BROKER: "Гаалийн брокер",
            PositionalCategory.CUSTOMS_OFFICER: "Гаалийн ажилтан",
            PositionalCategory.CUTTER_GRINDER_POLISHER: "Огтолч/Зүлгүүрч/Гялалгаагч",
            PositionalCategory.DTP_OPERATOR: "DTP оператор",
            PositionalCategory.DAMAGE_APPRAISER: "Хохирол үнэлгээч",
            PositionalCategory.DANCER: "Бүжигчин",
            PositionalCategory.DATA_ENTRY_OPERATOR: "Өгөгдөл оруулагч оператор",
            PositionalCategory.DATA_PROTECTION_OFFICER: "Өгөгдөл хамгаалалтын ажилтан",
            PositionalCategory.DATA_STATION_TESTING_SPECIALIST: "Өгөгдлийн станцын туршилтын мэргэжилтэн",
            PositionalCategory.DATA_ANALYST: "Өгөгдлийн шинжээч",
            PositionalCategory.DATA_COMMUNICATION_TECHNICIAN: "Өгөгдлийн харилцааны техникч",
            PositionalCategory.DATA_SCIENTIST: "Өгөгдлийн эрдэмтэн",
            PositionalCategory.DATABASE_ADMINISTRATOR: "Мэдээллийн сангийн администратор",
            PositionalCategory.DATABASE_ANALYST: "Мэдээллийн сангийн шинжээч",
            PositionalCategory.DEALER_TRADER: "Дилер/Трейдер",
            PositionalCategory.DENTAL_ASSISTANT: "Шүдний эмчийн туслах",
            PositionalCategory.DENTAL_HYGIENIST: "Шүдний эрүүл ахуйн мэргэжилтэн",
            PositionalCategory.DENTAL_TECHNICIAN: "Шүдний техникч",
            PositionalCategory.DENTIST: "Шүдний эмч",
            PositionalCategory.DEPARTMENT_DIRECTOR: "Хэлтсийн захирал",
            PositionalCategory.DEPARTMENT_MANAGER: "Хэлтсийн менежер",
            PositionalCategory.DEPUTY_HEADMASTER: "Захирлын орлогч",
            PositionalCategory.DEPUTY_SHOP_MANAGER: "Дэлгүүрийн менежерийн орлогч",
            PositionalCategory.DESIGN_ENGINEER: "Зураг төслийн инженер",
            PositionalCategory.DESIGN_TECHNICIAN: "Зураг төслийн техникч",
            PositionalCategory.DESIGN_ASSOCIATE: "Зураг төслийн нэгдэл",
            PositionalCategory.DESIGN_MANAGER: "Зураг төслийн менежер",
            PositionalCategory.DESIGNER: "Дизайнер",
            PositionalCategory.DEVELOPMENT_DIRECTOR: "Хөгжлийн захирал",
            PositionalCategory.DEVOPS_ENGINEER: "DevOps инженер",
            PositionalCategory.DIAGNOSTIC_TECHNICIAN: "Оношлогооны техникч",
            PositionalCategory.DIGITAL_MARKETING_MANAGER: "Дижитал маркетингийн менежер",
            PositionalCategory.DIGITAL_MARKETING_SPECIALIST: "Дижитал маркетингийн мэргэжилтэн",
            PositionalCategory.DISPATCH_CLERK: "Диспетчерийн ажилтан",
            PositionalCategory.DISPENSING_OPTICIAN: "Нүдний шилний мэргэжилтэн",
            PositionalCategory.DISTRIBUTION_CLERK: "Түгээлтийн ажилтан",
            PositionalCategory.DISTRICT_FOREST_OFFICER: "Дүүргийн ойн ажилтан",
            PositionalCategory.DIVERSITY_EQUITY_AND_INCLUSION_MANAGER: "Олон талт байдал, Тэгш байдал ба Оролцооны менежер",
            PositionalCategory.DOCTOR: "Эмч",
            PositionalCategory.DOCTOR_APPRENTICE: "Эмчийн шавь",
            PositionalCategory.DRIVER: "Жолооч",
            PositionalCategory.DRIVING_INSTRUCTOR: "Жолооны сургалтын багш",
            PositionalCategory.DRUG_SAFETY_SPECIALIST: "Эмийн аюулгүй байдлын мэргэжилтэн",
            PositionalCategory.E_COMMERCE_MANAGER: "Цахим худалдааны менежер",
            PositionalCategory.E_COMMERCE_SPECIALIST: "Цахим худалдааны мэргэжилтэн",
            PositionalCategory.ERP_PROGRAMMER: "ERP программист",
            PositionalCategory.ESG_MANAGER: "ESG менежер",
            PositionalCategory.ECOLOGIST: "Экологич",
            PositionalCategory.ECONOMIC_FINANCIAL_MANAGER: "Эдийн засаг/санхүүгийн менежер",
            PositionalCategory.ECONOMIST: "Эдийн засагч",
            PositionalCategory.EDITOR: "Редактор",
            PositionalCategory.EDITOR_IN_CHIEF: "Ерөнхий редактор",
            PositionalCategory.EDUCATION_COORDINATOR: "Боловсролын зохицуулагч",
            PositionalCategory.EDUCATION_SPECIALIST: "Боловсролын мэргэжилтэн",
            PositionalCategory.EDUCATOR_INSTRUCTOR_CARER: "Боловсролч/Зааварлагч/Асрагч",
            PositionalCategory.ELECTRICAL_ENGINEER: "Цахилгааны инженер",
            PositionalCategory.ELECTRICAL_ENGINEERING_TECHNICIAN: "Цахилгааны инженерийн техникч",
            PositionalCategory.ELECTRICAL_FITTER: "Цахилгааны угсрагч",
            PositionalCategory.ELECTRICIAN: "Цахилгаанч",
            PositionalCategory.ELECTRICIAN_INDUSTRIAL: "Цахилгаанч (үйлдвэрийн)",
            PositionalCategory.ELECTRONICS_ELECTRICIAN: "Электроникийн цахилгаанч",
            PositionalCategory.ENGINE_DRIVER: "Хөдөлгүүрийн жолооч",
            PositionalCategory.ENVIRONMENTALIST: "Байгаль орчны мэргэжилтэн",
            PositionalCategory.ESTATE_AGENT: "Үл хөдлөх хөрөнгийн агент",
            PositionalCategory.EVENT_MANAGER: "Арга хэмжээний менежер",
            PositionalCategory.EXPERT_SHOP_ASSISTANT: "Мэргэжлийн дэлгүүрийн туслах",
            PositionalCategory.FABRIC_CUTTER: "Даавуу огтолч",
            PositionalCategory.FACILITY_MANAGER: "Байгууламжийн менежер",
            PositionalCategory.FASHION_DESIGNER_PATTERN_CUTTER: "Загварч, Загварын огтолч",
            PositionalCategory.FAST_FOOD_WORKER: "Хурдан хоолны ажилтан",
            PositionalCategory.FILM_EDITOR: "Киноны редактор",
            PositionalCategory.FINANCE_MANAGER: "Санхүүгийн менежер",
            PositionalCategory.FINANCIAL_ADVISOR: "Санхүүгийн зөвлөх",
            PositionalCategory.FINANCIAL_AGENT: "Санхүүгийн агент",
            PositionalCategory.FINANCIAL_ANALYST: "Санхүүгийн шинжээч",
            PositionalCategory.FINANCIAL_MARKETS_SPECIALIST: "Санхүүгийн зах зээлийн мэргэжилтэн",
            PositionalCategory.FINANCIAL_ADMINISTRATION_ASSISTANT: "Санхүүгийн захиргааны туслах",
            PositionalCategory.FINISHING_WORKS_IN_CONSTRUCTIONS: "Барилгын дуусгалтын ажил",
            PositionalCategory.FIRE_OFFICER: "Гал түймэрийн ажилтан",
            PositionalCategory.FIREFIGHTER_RESCUER: "Гал унтраагч, Аврагч",
            PositionalCategory.FITNESS_INSTRUCTOR: "Фитнессийн зааварлагч",
            PositionalCategory.FITTER_ASSEMBLER: "Угсрагч",
            PositionalCategory.FLIGHT_ATTENDANT: "Нислэгийн бүртгэгч",
            PositionalCategory.FLOOR_LAYER_PAVER: "Шалны тавигч",
            PositionalCategory.FLORIST: "Цэцгийн дэлгүүрийн ажилтан",
            PositionalCategory.FOOD_ENGINEER: "Хүнсний инженер",
            PositionalCategory.FOOD_TECHNICIAN: "Хүнсний техникч",
            PositionalCategory.FOOD_TECHNOLOGIST: "Хүнсний технологич",
            PositionalCategory.FOREST_ENGINEER: "Ойн инженер",
            PositionalCategory.FOREST_TECHNICIAN: "Ойн техникч",
            PositionalCategory.FORESTER: "Ойч",
            PositionalCategory.FORESTRY_MANAGER: "Ойн аж ахуйн менежер",
            PositionalCategory.FOREMAN: "Ахлах ажилтан",
            PositionalCategory.FORKLIFT_TRUCK_OPERATOR: "Форклифтийн оператор",
            PositionalCategory.FORWARDER: "Экспедитор",
            PositionalCategory.FOUNDRY_WORKER: "Цутгалтын ажилтан",
            PositionalCategory.FRONTEND_DEVELOPER: "Фронтэнд хөгжүүлэгч",
            PositionalCategory.FUNERAL_SERVICE_WORKER: "Оршуулгын үйлчилгээний ажилтан",
            PositionalCategory.GAME_DESIGNER: "Тоглоомын дизайнер",
            PositionalCategory.GAME_DEVELOPER: "Тоглоомын хөгжүүлэгч",
            PositionalCategory.GARDENER: "Цэцэрлэгч",
            PositionalCategory.GENERAL_LABOURER: "Ерөнхий хөдөлмөрчин",
            PositionalCategory.GENERAL_STATE_ADVISOR: "Улсын ерөнхий зөвлөх",
            PositionalCategory.GEOGRAPHIC_INFORMATION_SYSTEMS_ENGINEER: "Газарзүйн мэдээллийн системийн инженер",
            PositionalCategory.GEOLOGIST: "Геологич",
            PositionalCategory.GEOTECHNICAL_INVESTIGATOR: "Геотехникийн судлаач",
            PositionalCategory.GLASSMAKER: "Шилчин",
            PositionalCategory.GO_DEVELOPER: "Go хөгжүүлэгч",
            PositionalCategory.GOLDSMITH_JEWELLER: "Алтны дархан, Үнэт эдлэлч",
            PositionalCategory.GRAIN_RECEIVER: "Үр тарианы хүлээн авагч",
            PositionalCategory.GRAPHIC: "График",
            PositionalCategory.GRAPHIC_DESIGNER: "График дизайнер",
            PositionalCategory.GUIDE_IN_THE_MUSEUM_GALLERY_CASTLE: "Музей, галерей, цайзны хөтөч",
            PositionalCategory.HR_ASSISTANT: "Хүний нөөцийн туслах",
            PositionalCategory.HR_BUSINESS_PARTNER: "Хүний нөөцийн бизнес түнш",
            PositionalCategory.HR_CONSULTANT: "Хүний нөөцийн зөвлөх",
            PositionalCategory.HR_COORDINATOR: "Хүний нөөцийн зохицуулагч",
            PositionalCategory.HR_GENERALIST: "Хүний нөөцийн ерөнхий мэргэжилтэн",
            PositionalCategory.HR_MANAGER: "Хүний нөөцийн менежер",
            PositionalCategory.HR_OFFICER: "Хүний нөөцийн ажилтан",
            PositionalCategory.HAIRDRESSER: "Үсчин",
            PositionalCategory.HEAD_NURSE: "Ахлах сувилагч",
            PositionalCategory.HEAD_PHARMACIST: "Ахлах эм зүйч",
            PositionalCategory.HEAD_OF_CUSTOMER_SUPPORT: "Үйлчлүүлэгчийн дэмжлэгийн дарга",
            PositionalCategory.HEAD_OF_TECHNICAL_DEPARTMENT: "Техникийн хэлтсийн дарга",
            PositionalCategory.HEAD_OF_VEHICLE_TECHNICAL_INSPECTION: "Тээврийн хэрэгслийн техникийн үзлэгийн дарга",
            PositionalCategory.HEAD_OF_CONTROLLING: "Хяналтын хэлтсийн дарга",
            PositionalCategory.HEAD_OF_PRODUCT_DEVELOPMENT: "Бүтээгдэхүүн хөгжүүлэлтийн дарга",
            PositionalCategory.HEAD_OF_THE_LEGAL_DEPARTMENT: "Хуулийн хэлтсийн дарга",
            PositionalCategory.HEALTH_CARE_ASSISTANT: "Эрүүл мэндийн тусламжийн ажилтан",
            PositionalCategory.HEALTH_CARE_PURCHASING_SPECIALIST: "Эрүүл мэндийн худалдан авалтын мэргэжилтэн",
            PositionalCategory.HEALTH_PROGRAM_DEVELOPMENT_SPECIALIST: "Эрүүл мэндийн хөтөлбөр хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.HEALTH_AND_SAFETY_OFFICER: "Эрүүл мэнд, Аюулгүй байдлын ажилтан",
            PositionalCategory.HELPDESK_OPERATOR: "Тусламжийн ширээний оператор",
            PositionalCategory.HOSTESS: "Хостесс",
            PositionalCategory.HOTEL_PORTER: "Зочид буудлын портье",
            PositionalCategory.HOTEL_MANAGER: "Зочид буудлын менежер",
            PositionalCategory.HOUSEKEEPER: "Гэрийн үйлчлэгч",
            PositionalCategory.HOUSEKEEPING_SUPERVISOR: "Гэр ахуйн ажлын ахлагч",
            PositionalCategory.HOUSEMAN: "Гэрийн ажилтан",
            PositionalCategory.IC_DESIGN_ENGINEER: "IC зураг төслийн инженер",
            PositionalCategory.ICT_SPECIALIST: "МХТ-ийн мэргэжилтэн",
            PositionalCategory.IFRS_SPECIALIST: "НББОУС-ийн мэргэжилтэн",
            PositionalCategory.ISO_SPECIALIST: "ISO мэргэжилтэн",
            PositionalCategory.IT_ANALYST: "МТ-ийн шинжээч",
            PositionalCategory.IT_ARCHITECT: "МТ-ийн архитектор",
            PositionalCategory.IT_BUSINESS_ANALYST: "МТ-ийн бизнес шинжээч",
            PositionalCategory.IT_CONSULTANT: "МТ-ийн зөвлөх",
            PositionalCategory.IT_DIRECTOR: "МТ-ийн захирал",
            PositionalCategory.IT_MANAGER: "МТ-ийн менежер",
            PositionalCategory.IT_NETWORK_ADMINISTRATOR: "МТ-ийн сүлжээний администратор",
            PositionalCategory.IT_PRODUCT_MANAGER: "МТ-ийн бүтээгдэхүүний менежер",
            PositionalCategory.IT_PROJECT_MANAGER: "МТ-ийн төслийн менежер",
            PositionalCategory.IT_SECURITY_SPECIALIST: "МТ-ийн аюулгүй байдлын мэргэжилтэн",
            PositionalCategory.IT_SYSTEM_ADMINISTRATOR: "МТ-ийн системийн администратор",
            PositionalCategory.IT_TESTER: "МТ-ийн тестер",
            PositionalCategory.IT_AUDITOR: "МТ-ийн аудитор",
            PositionalCategory.IT_TESTER_AUTOMATED_TESTS: "МТ-ийн тестер - автомат тест",
            PositionalCategory.IT_TECHNICAL_SUPPORT_SPECIALIST: "МТ/Техникийн дэмжлэгийн мэргэжилтэн",
            PositionalCategory.IMAGE_STYLIST_BEAUTY_STYLIST: "Дүр төрхийн стилист, Гоо сайханы стилист",
            PositionalCategory.IMPORT_EXPORT_OFFICER: "Импорт/экспортын ажилтан",
            PositionalCategory.INCIDENT_MANAGER: "Аваарын менежер",
            PositionalCategory.INDEPENDENT_ADVISOR: "Бие даасан зөвлөх",
            PositionalCategory.INDEPENDENT_EXPERT_ASSOCIATE: "Бие даасан мэргэжилтэн",
            PositionalCategory.INDEPENDENT_OFFICIAL: "Бие даасан албан тушаалтан",
            PositionalCategory.INDUSTRIAL_CLIMBER: "Үйлдвэрийн альпинист",
            PositionalCategory.INDUSTRIAL_PAINTER: "Үйлдвэрийн будагч",
            PositionalCategory.INSPECTOR: "Байцаагч",
            PositionalCategory.INSURANCE_BROKER: "Даатгалын брокер",
            PositionalCategory.INSURANCE_PAYMENT_CONTROL_SPECIALIST: "Даатгалын төлбөрийн хяналтын мэргэжилтэн",
            PositionalCategory.INSURANCE_TECHNICIAN: "Даатгалын техникч",
            PositionalCategory.INSURANCE_UNDERWRITER: "Даатгалын андеррайтер",
            PositionalCategory.INSURANCE_ADMINISTRATOR: "Даатгалын администратор",
            PositionalCategory.INTERIOR_DESIGNER: "Интерьер дизайнер",
            PositionalCategory.INTERNAL_AUDITOR: "Дотоод аудитор",
            PositionalCategory.INTERNAL_COMMUNICATION_SPECIALIST: "Дотоод харилцааны мэргэжилтэн",
            PositionalCategory.INTERPRETER: "Орчуулагч",
            PositionalCategory.INVOICING_AND_PAYMENT_SPECIALIST: "Нэхэмжлэх, Төлбөрийн мэргэжилтэн",
            PositionalCategory.IRON_FOUNDER: "Төмрийн цутгагч",
            PositionalCategory.IRONWORKER: "Төмөрчин",
            PositionalCategory.JAVA_PROGRAMMER: "Java программист",
            PositionalCategory.JAVASCRIPT_PROGRAMMER: "Javascript программист",
            PositionalCategory.JOINER: "Модон эдлэлчин",
            PositionalCategory.JUDGE: "Шүүгч",
            PositionalCategory.JUDICIAL_ASSISTANT: "Шүүхийн туслах",
            PositionalCategory.JUNIOR_ACCOUNTANT: "Дэд нягтлан бодогч",
            PositionalCategory.JUNIOR_ARCHITECT: "Дэд архитектор",
            PositionalCategory.JUNIOR_GRAPHIC_DESIGNER: "Дэд график дизайнер",
            PositionalCategory.JUNIOR_PROJECT_MANAGER: "Дэд төслийн менежер",
            PositionalCategory.JUNIOR_SALES_REPRESENTATIVE: "Дэд борлуулалтын төлөөлөгч",
            PositionalCategory.JUNIOR_STATISTICIAN: "Дэд статистикч",
            PositionalCategory.KEY_ACCOUNT_MANAGER: "Гол дансны менежер",
            PositionalCategory.KINETOTHERAPIST: "Кинетотерапевт",
            PositionalCategory.KITCHEN_DESIGNER: "Гал тогооны дизайнер",
            PositionalCategory.KITCHEN_HELPER: "Гал тогооны туслах",
            PositionalCategory.LABORATORY_DIRECTOR: "Лабораторийн захирал",
            PositionalCategory.LABORATORY_TECHNICIAN: "Лабораторийн техникч",
            PositionalCategory.LAND_SURVEYOR_GEODESIST: "Газрын хэмжигч/Геодезист",
            PositionalCategory.LANDSCAPE_ARCHITECT: "Ландшафтын архитектор",
            PositionalCategory.LATHE_OPERATOR: "Токарь оператор",
            PositionalCategory.LABOURER: "Хөдөлмөрчин",
            PositionalCategory.LAWYER: "Хуульч",
            PositionalCategory.LEAD_DEVELOPER: "Ахлах хөгжүүлэгч",
            PositionalCategory.LEASING_CONSULTANT: "Лизингийн зөвлөх",
            PositionalCategory.LEASING_DIRECTOR: "Лизингийн захирал",
            PositionalCategory.LECTOR: "Лектор",
            PositionalCategory.LECTURER_TRAINER: "Лектор, Сургагч",
            PositionalCategory.LEGAL_ADVISOR: "Хуулийн зөвлөх",
            PositionalCategory.LIBRARIAN: "Номын сангийн ажилтан",
            PositionalCategory.LIFEGUARD_SWIMMING_INSTRUCTOR: "Аврагч, Усны спортын зааварлагч",
            PositionalCategory.LIGHTING_TECHNICIAN: "Гэрлийн техникч",
            PositionalCategory.LIVESTOCK_SPECIALIST: "Мал аж ахуйн мэргэжилтэн",
            PositionalCategory.LOAN_SPECIALIST: "Зээлийн мэргэжилтэн",
            PositionalCategory.LOGISTICS_CLERK: "Логистикийн ажилтан",
            PositionalCategory.LOGISTICS_CONTROLLER: "Логистикийн хянагч",
            PositionalCategory.LOGISTICS_DIRECTOR: "Логистикийн захирал",
            PositionalCategory.LOGISTICS_MANAGER: "Логистикийн менежер",
            PositionalCategory.LORRY_DRIVER: "Ачааны машины жолооч",
            PositionalCategory.LOSS_ADJUSTER: "Алдагдлын үнэлгээч",
            PositionalCategory.LUMBERJACK: "Модчин",
            PositionalCategory.MACHINE_FITTER: "Машины угсрагч",
            PositionalCategory.MACHINE_OPERATOR: "Машины оператор",
            PositionalCategory.MACHINE_OPERATOR_MACHINIST: "Машины оператор, Машинист",
            PositionalCategory.MACHINE_SETTER: "Машины тохируулагч",
            PositionalCategory.MAINENTENANCE_WORKER: "Засвар үйлчилгээний ажилтан",
            PositionalCategory.MAINTENANCE_ENGINEER: "Засвар үйлчилгээний инженер",
            PositionalCategory.MAINTENANCE_SUPERVISOR: "Засвар үйлчилгээний ахлагч",
            PositionalCategory.MAINTENANCE_WORKER: "Засвар үйлчилгээний ажилтан",
            PositionalCategory.MAKE_UP_ARTIST_WIGMAKER: "Гримчин, Үсний дизайнер",
            PositionalCategory.MANAGING_DIRECTOR: "Гүйцэтгэх захирал",
            PositionalCategory.MANAGING_EDITOR: "Менежер редактор",
            PositionalCategory.MARITIME_TRANSPORT_ORGANISER: "Далайн тээврийн зохион байгуулагч",
            PositionalCategory.MARKETING_ANALYST: "Маркетингийн шинжээч",
            PositionalCategory.MARKETING_DIRECTOR: "Маркетингийн захирал",
            PositionalCategory.MARKETING_MANAGER: "Маркетингийн менежер",
            PositionalCategory.MARKETING_OFFICER: "Маркетингийн ажилтан",
            PositionalCategory.MARKETING_SPECIALIST: "Маркетингийн мэргэжилтэн",
            PositionalCategory.MARKETING_ASSISTANT: "Маркетингийн туслах",
            PositionalCategory.MASTER_IN_VOCATIONAL_EDUCATION: "Мэргэжлийн боловсролын мастер",
            PositionalCategory.MASSEUR: "Массажист",
            PositionalCategory.MECHANICAL_DESIGN_ENGINEER_AUTOMATION: "Механик зураг төслийн инженер - Автоматжуулалт",
            PositionalCategory.MECHANICAL_ENGINEER: "Механик инженер",
            PositionalCategory.MECHANIZATION_MANAGER: "Механикжуулалтын менежер",
            PositionalCategory.MEDIA_BUYER: "Медиа худалдан авагч",
            PositionalCategory.MEDIA_PLANNER: "Медиа төлөвлөгч",
            PositionalCategory.MEDICAL_ADVISOR: "Анагаах ухааны зөвлөх",
            PositionalCategory.MEDICAL_INSTITUTION_MANAGER: "Эмнэлгийн байгууллагын менежер",
            PositionalCategory.MEDICAL_LABORATORY_TECHNICIAN: "Анагаах ухааны лабораторийн техникч",
            PositionalCategory.MEDICAL_ORDERLY: "Эмнэлгийн санитар",
            PositionalCategory.MEDICAL_RECORDS_CLERK: "Эмнэлгийн бүртгэлийн ажилтан",
            PositionalCategory.MEDICAL_ASSISTANT: "Эмнэлгийн туслах",
            PositionalCategory.MEDICAL_GRADUATE: "Анагаахын төгсөгч",
            PositionalCategory.MEDICAL_PHARMACEUTICAL_SALES_REPRESENTATIVE: "Анагаах/Эмийн борлуулалтын төлөөлөгч",
            PositionalCategory.MECHATRONICS_TECHNICIAN: "Мехатроникийн техникч",
            PositionalCategory.METALLURGIST: "Металлургич",
            PositionalCategory.METALLURGY_ENGINEER: "Металлургийн инженер",
            PositionalCategory.METALWORKER: "Металлчин",
            PositionalCategory.METEOROLOGIST: "Цаг уурч",
            PositionalCategory.METROLOGIST: "Метрологич",
            PositionalCategory.MICROBIOLOGIST: "Микробиологич",
            PositionalCategory.MICROCONTROLLER_PROGRAMMER: "Микроконтроллерийн программист",
            PositionalCategory.MIDWIFE: "Акушер",
            PositionalCategory.MILKER: "Сааль саагч",
            PositionalCategory.MILLING_MACHINE_OPERATOR: "Фрезийн машины оператор",
            PositionalCategory.MINER: "Уурхайч",
            PositionalCategory.MINING_ENGINEER: "Уул уурхайн инженер",
            PositionalCategory.MINING_MANAGER: "Уул уурхайн менежер",
            PositionalCategory.MINING_TECHNICIAN: "Уул уурхайн техникч",
            PositionalCategory.MOBILE_NETWORK_DEVELOPMENT_SPECIALIST: "Гар утасны сүлжээ хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.MODEL: "Загварчин",
            PositionalCategory.MORTGAGE_SPECIALIST: "Ипотекийн мэргэжилтэн",
            PositionalCategory.MUSIC_AND_ART_SCHOOL_TEACHER: "Хөгжим, Урлагийн сургуулийн багш",
            PositionalCategory.NANNY: "Хүүхэд харагч",
            PositionalCategory.NAVAL_OFFICER: "Тэнгисийн офицер",
            PositionalCategory.NETWORK_MODELLING_SPECIALIST: "Сүлжээний загварчлалын мэргэжилтэн",
            PositionalCategory.NETWORK_STRATEGY_SPECIALIST: "Сүлжээний стратегийн мэргэжилтэн",
            PositionalCategory.NETWORK_AND_SERVICE_OPERATION_SPECIALIST: "Сүлжээ ба үйлчилгээний үйл ажиллагааны мэргэжилтэн",
            PositionalCategory.NOTARY: "Нотариат",
            PositionalCategory.NOTARY_ASSOCIATE: "Нотариатын туслах",
            PositionalCategory.NURSE: "Сувилагч",
            PositionalCategory.NURSERY_SCHOOL_TEACHER_ASSISTANT: "Цэцэрлэгийн багшийн туслах",
            PositionalCategory.NUTRITION_ASSISTANT: "Хоол тэжээлийн туслах",
            PositionalCategory.OSS_BSS_SPECIALIST: "OSS/BSS мэргэжилтэн",
            PositionalCategory.OBJECTIVE_C_PROGRAMMER: "Objective-C программист",
            PositionalCategory.OCCUPATIONAL_PSYCHOLOGIST: "Хөдөлмөрийн сэтгэл зүйч",
            PositionalCategory.OCCUPATIONAL_HEALTH_NURSE: "Хөдөлмөрийн эрүүл мэндийн сувилагч",
            PositionalCategory.OFFICE_MANAGER: "Оффисын менежер",
            PositionalCategory.OFFICIAL: "Албан тушаалтан",
            PositionalCategory.ONLINE_SHOP_ADMINISTRATOR: "Онлайн дэлгүүрийн администратор",
            PositionalCategory.OPERATIONS_MANAGER: "Үйл ажиллагааны менежер",
            PositionalCategory.OPERATIONS_SUPERVISOR: "Үйл ажиллагааны ахлагч",
            PositionalCategory.OPTOMETRIST: "Оптометрист",
            PositionalCategory.ORACLE_PROGRAMMER: "Oracle программист",
            PositionalCategory.ORGANIZER: "Зохион байгуулагч",
            PositionalCategory.ORTHOPEDIC_TECHNICIAN: "Ортопедийн техникч",
            PositionalCategory.PHP_PROGRAMMER: "PHP программист",
            PositionalCategory.PLC_PROGRAMMER: "PLC программист",
            PositionalCategory.PPC_SPECIALIST: "PPC мэргэжилтэн",
            PositionalCategory.PR_MANAGER: "PR менежер",
            PositionalCategory.PC_TECHNICIAN: "Компьютерийн техникч",
            PositionalCategory.PACKER: "Савлагч",
            PositionalCategory.PAINTER: "Будагч",
            PositionalCategory.PARALEGAL_LAW_STUDENT: "Хуулийн туслах - хуулийн оюутан",
            PositionalCategory.PASTRY_CHEF_CONFECTIONER: "Бялуучин, Чихэрлэг хоолны тогооч",
            PositionalCategory.PAYROLL_CLERK: "Цалингийн ажилтан",
            PositionalCategory.PEDAGOGUE: "Багш, Сурган хүмүүжүүлэгч",
            PositionalCategory.PEDICURIST_MANICURIST_NAIL_TECHNICIAN: "Педикюрист, Маникюрист, Хумсны техникч",
            PositionalCategory.PERL_PROGRAMMER: "Perl программист",
            PositionalCategory.PERSONAL_BANKER: "Хувийн банкир",
            PositionalCategory.PERSONNEL_MANAGER: "Персоналийн менежер",
            PositionalCategory.PETROL_STATION_ATTENDANT: "Шатахуун түгээгч",
            PositionalCategory.PETROLEUM_ENGINEER: "Газрын тосны инженер",
            PositionalCategory.PHARMACEUTICAL_LABORATORY_TECHNICIAN: "Эмийн лабораторийн техникч",
            PositionalCategory.PHARMACEUTICAL_PRODUCTS_MANAGER: "Эмийн бүтээгдэхүүний менежер",
            PositionalCategory.PHARMACIST: "Эм зүйч",
            PositionalCategory.PHARMACIST_ASSISTANT: "Эм зүйчийн туслах",
            PositionalCategory.PHOTO_EDITOR: "Фото редактор",
            PositionalCategory.PHOTOGRAPHER: "Гэрэл зурагчин",
            PositionalCategory.PHYSIOTHERAPIST: "Физик эмчилгээч",
            PositionalCategory.PICKER: "Сонгогч",
            PositionalCategory.PILOT: "Нисгэгч",
            PositionalCategory.PIPE_FITTER: "Хоолойчин",
            PositionalCategory.PIZZA_COOK: "Пицца тогооч",
            PositionalCategory.PLANNING_ASSISTANT: "Төлөвлөлтийн туслах",
            PositionalCategory.PLANT_MANAGER: "Үйлдвэрийн менежер",
            PositionalCategory.PLUMBER: "Сантехникч",
            PositionalCategory.POLICE_INSPECTOR: "Цагдаагийн байцаагч",
            PositionalCategory.POLICE_OFFICER: "Цагдаа",
            PositionalCategory.POSTAL_DELIVERY_WORKER: "Шуудангийн хүргэлтийн ажилтан",
            PositionalCategory.POSTAL_WORKER: "Шуудангийн ажилтан",
            PositionalCategory.POSTMASTER: "Шуудангийн дарга",
            PositionalCategory.POWER_ENGINEER: "Эрчим хүчний инженер",
            PositionalCategory.POWER_GENERATING_MACHINERY_OPERATOR: "Эрчим хүч үйлдвэрлэх машины оператор",
            PositionalCategory.PRE_SCHOOL_SCHOOL_KINDERGARDER_NURSE: "Сургуулийн өмнөх боловсролын/Цэцэрлэгийн сувилагч",
            PositionalCategory.PRESCHOOL_TEACHER: "Цэцэрлэгийн багш",
            PositionalCategory.PRIMARY_SCHOOL_TEACHER: "Бага сургуулийн багш",
            PositionalCategory.PRIEST: "Лам, Санваартан",
            PositionalCategory.PRINTER: "Хэвлэгч",
            PositionalCategory.PRINTING_TECHNICIAN: "Хэвлэлийн техникч",
            PositionalCategory.PRISON_OFFICER: "Шорон хорих газрын ажилтан",
            PositionalCategory.PRIVATE_BANKER: "Хувийн банкир",
            PositionalCategory.PROBLEM_MANAGER: "Асуудлын менежер",
            PositionalCategory.PROCESS_ENGINEER: "Процессын инженер",
            PositionalCategory.PROCESS_MANAGER: "Процессын менежер",
            PositionalCategory.PROCUREMENT_SPECIALIST: "Худалдан авалтын мэргэжилтэн",
            PositionalCategory.PRODUCER: "Продюсер",
            PositionalCategory.PRODUCT_DEVELOPMENT_SPECIALIST: "Бүтээгдэхүүн хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.PRODUCT_MANAGER_SPECIALIST: "Бүтээгдэхүүний менежер - Мэргэжилтэн",
            PositionalCategory.PRODUCT_MARKETING_MANAGER: "Бүтээгдэхүүний маркетингийн менежер",
            PositionalCategory.PRODUCT_OWNER: "Бүтээгдэхүүний эзэн",
            PositionalCategory.PRODUCTION_DIRECTOR: "Үйлдвэрлэлийн захирал",
            PositionalCategory.PRODUCTION_MANAGER: "Үйлдвэрлэлийн менежер",
            PositionalCategory.PRODUCTION_PLANNER: "Үйлдвэрлэлийн төлөвлөгч",
            PositionalCategory.PRODUCTION_STANDARD_SETTER: "Үйлдвэрлэлийн стандарт тогтоогч",
            PositionalCategory.PRODUCTION_SUPERVISOR: "Үйлдвэрлэлийн ахлагч",
            PositionalCategory.PROFESSOR: "Профессор",
            PositionalCategory.PROGRAMMER: "Программист",
            PositionalCategory.PROJECT_ASSISTANT: "Төслийн туслах",
            PositionalCategory.PROJECT_COORDINATOR: "Төслийн зохицуулагч",
            PositionalCategory.PROJECT_MANAGER: "Төслийн менежер",
            PositionalCategory.PROJECT_PLANNER: "Төслийн төлөвлөгч",
            PositionalCategory.PROMOTIONAL_ASSISTANT: "Сурталчилгааны туслах",
            PositionalCategory.PROOFREADER: "Эх засагч",
            PositionalCategory.PROPERTY_MANAGER: "Өмчийн менежер",
            PositionalCategory.PROSECUTOR: "Прокурор",
            PositionalCategory.PSYCHOLOGIST: "Сэтгэл зүйч",
            PositionalCategory.PUBLIC_HEALTH_ADMINISTRATOR: "Нийгмийн эрүүл мэндийн администратор",
            PositionalCategory.PUBLISHING_HOUSE_DIRECTOR: "Хэвлэлийн газрын захирал",
            PositionalCategory.PURCHASING_MANAGER: "Худалдан авалтын менежер",
            PositionalCategory.PYTHON_PROGRAMMER: "Python программист",
            PositionalCategory.QUALITY_CONTROL_ISO_MANAGER: "Чанарын хяналт/ISO менежер",
            PositionalCategory.QUALITY_ENGINEER: "Чанарын инженер",
            PositionalCategory.QUALITY_INSPECTOR: "Чанарын байцаагч",
            PositionalCategory.QUALITY_MANAGER: "Чанарын менежер",
            PositionalCategory.QUALITY_PLANNER: "Чанарын төлөвлөгч",
            PositionalCategory.QUALIFIED_MECHANICAL_ENGINEER: "Мэргэшсэн механик инженер",
            PositionalCategory.QUANTITY_SURVEYOR: "Тооцооны инженер",
            PositionalCategory.R_PROGRAMMER: "R программист",
            PositionalCategory.RADIO_NETWORK_OPTIMIZATION_SPECIALIST: "Радио сүлжээний оновчлолын мэргэжилтэн",
            PositionalCategory.RADIO_NETWORK_PLANNING_SPECIALIST: "Радио сүлжээний төлөвлөлтийн мэргэжилтэн",
            PositionalCategory.RADIO_PRESENTER_AND_ANNOUNCER: "Радиогийн нэвтрүүлэгч",
            PositionalCategory.RADIOGRAPHER: "Рентген зурагч",
            PositionalCategory.RADIOLOGY_ASSISTANT: "Радиологийн туслах",
            PositionalCategory.RAIL_TRANSPORT_CONTROLLER_SHUNTER_SIGNALIST: "Төмөр замын хяналтын ажилтан (шунтер, сигналист)",
            PositionalCategory.REAL_ESTATE_APPRAISER: "Үл хөдлөх хөрөнгийн үнэлгээч",
            PositionalCategory.REAL_ESTATE_MAINTENANCE: "Үл хөдлөх хөрөнгийн засвар үйлчилгээ",
            PositionalCategory.RECEPTIONIST: "Хүлээн авалтын ажилтан",
            PositionalCategory.RECEPTIONIST_I: "Хүлээн авалтын ажилтан I",
            PositionalCategory.RECRUITER: "Элсэлтийн ажилтан",
            PositionalCategory.REFRIGERATION_MECHANIC: "Хөргөлтийн механик",
            PositionalCategory.REGIONAL_AREA_MANAGER: "Бүсийн менежер",
            PositionalCategory.REGIONAL_MANAGER: "Бүсийн менежер",
            PositionalCategory.REGISTRY_ADMINISTRATION_OFFICER: "Бүртгэлийн захиргааны ажилтан",
            PositionalCategory.REGULATORY_AFFAIRS_MANAGER: "Зохицуулалтын асуудлын менежер",
            PositionalCategory.REGULATORY_AFFAIRS_SPECIALIST: "Зохицуулалтын асуудлын мэргэжилтэн",
            PositionalCategory.REINSURANCE_SPECIALIST: "Дахин даатгалын мэргэжилтэн",
            PositionalCategory.RELATIONSHIP_MANAGER: "Харилцааны менежер",
            PositionalCategory.REPORTER: "Сурвалжлагч",
            PositionalCategory.REPORTING_SPECIALIST: "Тайлангийн мэргэжилтэн",
            PositionalCategory.REPAIRER: "Засварч",
            PositionalCategory.RESEARCH_PHYSICIAN: "Судалгааны эмч",
            PositionalCategory.RESEARCH_WORKER_SCIENTIFIC_WORKER: "Судалгааны ажилтан, Шинжлэх ухааны ажилтан",
            PositionalCategory.RESTAURANT_MANAGER: "Ресторанны менежер",
            PositionalCategory.RESTAURANT_WORKER: "Ресторанны ажилтан",
            PositionalCategory.RESTORER_CONSERVATOR: "Сэргээн засварлагч",
            PositionalCategory.RETAIL_STORE_MANAGER: "Жижиглэн худалдааны дэлгүүрийн менежер",
            PositionalCategory.RETURNS_DEPARTMENT_MANAGER: "Буцаалтын хэлтсийн менежер",
            PositionalCategory.RISK_MANAGER: "Рискийн менежер",
            PositionalCategory.RISK_SPECIALIST: "Рискийн мэргэжилтэн",
            PositionalCategory.ROAMING_SPECIALIST: "Роамингийн мэргэжилтэн",
            PositionalCategory.ROOFER: "Дээврийн ажилчин",
            PositionalCategory.RUBY_DEVELOPER_PROGRAMMER: "Ruby хөгжүүлэгч/программист",
            PositionalCategory.SAP_SPECIALIST: "SAP мэргэжилтэн",
            PositionalCategory.SEO_ANALYST: "SEO шинжээч",
            PositionalCategory.SAFETY_SPECIALIST: "Аюулгүй байдлын мэргэжилтэн",
            PositionalCategory.SAILOR: "Далайч",
            PositionalCategory.SALES_CONSULTANT: "Борлуулалтын зөвлөх",
            PositionalCategory.SALES_DIRECTOR: "Борлуулалтын захирал",
            PositionalCategory.SALES_ENGINEER: "Борлуулалтын инженер",
            PositionalCategory.SALES_MANAGER: "Борлуулалтын менежер",
            PositionalCategory.SALES_OBJECT_MANAGER: "Борлуулалтын объектын менежер",
            PositionalCategory.SALES_OFFICE_MANAGER: "Борлуулалтын оффисын менежер",
            PositionalCategory.SALES_OFFICER: "Борлуулалтын ажилтан",
            PositionalCategory.SALES_REPRESENTATIVE: "Борлуулалтын төлөөлөгч",
            PositionalCategory.SALES_COORDINATOR: "Борлуулалтын зохицуулагч",
            PositionalCategory.SAW_FILER: "Хөрөө засагч",
            PositionalCategory.SCAFFOLDER: "Тулгуур барилгач",
            PositionalCategory.SCHOOL_CANTEEN_MANAGER: "Сургуулийн гуанзны менежер",
            PositionalCategory.SCHOOL_CARETAKER: "Сургуулийн харуул хамгаалагч",
            PositionalCategory.SCHOOL_PRINCIPAL: "Сургуулийн захирал",
            PositionalCategory.SCRUM_MASTER: "Scrum Мастер",
            PositionalCategory.SEAMSTRESS: "Оёдолчин",
            PositionalCategory.SECONDARY_SCHOOL_TEACHER: "Дунд сургуулийн багш",
            PositionalCategory.SECRETARY: "Нарийн бичгийн дарга",
            PositionalCategory.SECRETARY_OF_HEALTH_DEPARTMENT: "Эрүүл мэндийн хэлтсийн нарийн бичгийн дарга",
            PositionalCategory.SECURITY_GUARD: "Харуул хамгаалагч",
            PositionalCategory.SECURITY_SERVICE_DIRECTOR: "Хамгаалалтын үйлчилгээний захирал",
            PositionalCategory.SECURITY_SERVICE_MANAGER: "Хамгаалалтын үйлчилгээний менежер",
            PositionalCategory.SECURITY_SERVICE_TECHNICIAN: "Хамгаалалтын үйлчилгээний техникч",
            PositionalCategory.SELLER_CASHIER: "Худалдагч / Кассир",
            PositionalCategory.SELLER_OF_BANK_SERVICES_LOAN_OFFICER: "Банкны үйлчилгээний худалдагч, Зээлийн ажилтан",
            PositionalCategory.SENIOR_ACCOUNTANT: "Ахлах нягтлан бодогч",
            PositionalCategory.SENIOR_ASSOCIATE: "Ахлах нэгдэл",
            PositionalCategory.SENIOR_GRAPHIC_DESIGNER: "Ахлах график дизайнер",
            PositionalCategory.SENIOR_PROJECT_MANAGER: "Ахлах төслийн менежер",
            PositionalCategory.SENIOR_SALES_REPRESENTATIVE: "Ахлах борлуулалтын төлөөлөгч",
            PositionalCategory.SENIOR_STATISTICIAN: "Ахлах статистикч",
            PositionalCategory.SERVICE_ENGINEER: "Үйлчилгээний инженер",
            PositionalCategory.SERVICE_TECHNICIAN: "Үйлчилгээний техникч",
            PositionalCategory.SHELF_STACKER_MERCHANDISER: "Тавиур дүүргэгч/Мерчандайзер",
            PositionalCategory.SHIFT_MANAGER: "Ээлжийн менежер",
            PositionalCategory.SHOP_ASSISTANT: "Дэлгүүрийн туслах",
            PositionalCategory.SHOP_WINDOW_DECORATOR: "Дэлгүүрийн цонхны чимэглэгч",
            PositionalCategory.SMITH: "Дархан",
            PositionalCategory.SOCIAL_COUNSELOR: "Нийгмийн зөвлөгч",
            PositionalCategory.SOCIAL_MEDIA_SPECIALIST: "Нийгмийн сүлжээний мэргэжилтэн",
            PositionalCategory.SOCIAL_REHABILITATION_SPECIALIST: "Нийгмийн нөхөн сэргээлтийн мэргэжилтэн",
            PositionalCategory.SOFTWARE_ENGINEER: "Програм хангамжийн инженер",
            PositionalCategory.SOFTWARE_CONSULTANT: "Програм хангамжийн зөвлөх",
            PositionalCategory.SOLDIER: "Цэрэг",
            PositionalCategory.SOLICITOR_BARRISTER: "Өмгөөлөгч",
            PositionalCategory.SOMMELIER: "Сомелье",
            PositionalCategory.SOUND_ENGINEER: "Дуу авианы инженер",
            PositionalCategory.SPA_THERAPIST: "Спа эмчилгээч",
            PositionalCategory.SPATIAL_PLANNER: "Орон зайн төлөвлөгч",
            PositionalCategory.SPECIAL_NEEDS_TEACHER: "Тусгай хэрэгцээт боловсролын багш",
            PositionalCategory.SPECIALIST_ADVISOR: "Мэргэжлийн зөвлөх",
            PositionalCategory.SPECIALIST_OFFICIAL: "Мэргэжлийн албан тушаалтан",
            PositionalCategory.SPEECH_THERAPIST: "Логопед",
            PositionalCategory.SPORTS_COACH: "Спортын дасгалжуулагч",
            PositionalCategory.SPORTS_COORDINATOR: "Спортын зохицуулагч",
            PositionalCategory.STAGEHAND: "Тайзны ажилтан",
            PositionalCategory.STATE_ADVISOR: "Улсын зөвлөх",
            PositionalCategory.STOCK_BROKER: "Хөрөнгийн брокер",
            PositionalCategory.STOKER_BOILER_ATTENDANT: "Зуухч",
            PositionalCategory.STONEMASON: "Чулуучин",
            PositionalCategory.STORE_DEPARTMENT_MANAGER: "Агуулахын хэлтсийн менежер",
            PositionalCategory.STOREKEEPER: "Агуулахын ажилтан",
            PositionalCategory.STRUCTURAL_ENGINEER: "Байгууламжийн инженер",
            PositionalCategory.SUPERINTENDENT: "Ерөнхий хянагч",
            PositionalCategory.SUPPLY_CHAIN_SPECIALIST: "Нийлүүлэлтийн гинжийн мэргэжилтэн",
            PositionalCategory.SUPPLY_TECHNICIAN: "Нийлүүлэлтийн техникч",
            PositionalCategory.SURVEY_INTERVIEWER: "Судалгааны ярилцлагч",
            PositionalCategory.SWITCHING_NETWORK_DEVELOPMENT_SPECIALIST: "Шилжүүлэлтийн сүлжээ хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.SYSTEMS_ADMINISTRATOR: "Системийн администратор",
            PositionalCategory.SYSTEMS_ENGINEER: "Системийн инженер",
            PositionalCategory.TV_PRESENTER: "ТВ нэвтрүүлэгч",
            PositionalCategory.TV_FILM_PRODUCTION_ASSISTANT: "ТВ/Киноны үйлдвэрлэлийн туслах",
            PositionalCategory.TAILOR: "Оёдолчин",
            PositionalCategory.TAX_ADVISOR: "Татварын зөвлөх",
            PositionalCategory.TAXI_DRIVER: "Таксины жолооч",
            PositionalCategory.TEACHER: "Багш",
            PositionalCategory.TEAM_LEADER: "Багийн ахлагч",
            PositionalCategory.TECHNICAL_DIRECTOR: "Техникийн захирал",
            PositionalCategory.TECHNICAL_MANAGER: "Техникийн менежер",
            PositionalCategory.TECHNICAL_STAFF: "Техникийн ажилтан",
            PositionalCategory.TECHNICAL_SUPPORT_SPECIALIST: "Техникийн дэмжлэгийн мэргэжилтэн",
            PositionalCategory.TECHNICAL_WRITER: "Техникийн бичгийн ажилтан",
            PositionalCategory.TECHNICAL_PRODUCT_ENGINEER: "Техникийн бүтээгдэхүүний инженер",
            PositionalCategory.TELECOMMUNICATION_SPECIALIST: "Харилцаа холбооны мэргэжилтэн",
            PositionalCategory.TELECOMMUNICATION_NETWORK_INSTALLER: "Харилцаа холбооны сүлжээ угсрагч",
            PositionalCategory.TELECOMMUNICATIONS_NETWORK_DESIGNER: "Харилцаа холбооны сүлжээний дизайнер",
            PositionalCategory.TELECOMMUNICATIONS_PRODUCT_DEVELOPMENT_SPECIALIST: "Харилцаа холбооны бүтээгдэхүүн хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.TELECOMMUNICATIONS_SERVICE_DEVELOPMENT_SPECIALIST: "Харилцаа холбооны үйлчилгээ хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.TELEMARKETER: "Утсаар маркетинг хийгч",
            PositionalCategory.TERMINAL_OPERATOR: "Терминалийн оператор",
            PositionalCategory.TESTING_MANAGER: "Туршилтын менежер",
            PositionalCategory.TECHNICIAN: "Техникч",
            PositionalCategory.TECHNOLOGIST: "Технологич",
            PositionalCategory.TILE_MAN: "Хавтанч",
            PositionalCategory.TIMBER_ENGINEER: "Модон материалын инженер",
            PositionalCategory.TOOLMAKER: "Хэрэгсэл үйлдвэрлэгч",
            PositionalCategory.TRAFFIC_CONTROLLER: "Замын хөдөлгөөний хяналтын ажилтан",
            PositionalCategory.TRAFFIC_ENGINEER: "Замын хөдөлгөөний инженер",
            PositionalCategory.TRAIN_CONDUCTOR: "Галт тэргний кондуктор",
            PositionalCategory.TRAIN_DISPATCHER: "Галт тэргний диспетчер",
            PositionalCategory.TRAINEE_BAILIFF: "Дадлагажигч биелэлтийн ажилтан",
            PositionalCategory.TRAM_DRIVER: "Трамвайн жолооч",
            PositionalCategory.TRANSMISSION_NETW_ANALYSIS_DEVELOPMENT_SPECIALIST: "Дамжуулалтын сүлжээний шинжилгээ ба хөгжүүлэлтийн мэргэжилтэн",
            PositionalCategory.TRANSPORT_MANAGER: "Тээврийн менежер",
            PositionalCategory.TRAVEL_GUIDE: "Аялалын хөтөч",
            PositionalCategory.TROLLEYBUS_DRIVER: "Троллейбусны жолооч",
            PositionalCategory.TUTOR: "Хувийн багш",
            PositionalCategory.TYRE_FITTER: "Дугуй угсрагч",
            PositionalCategory.UX_DESIGNER: "UX дизайнер",
            PositionalCategory.UNIVERSITY_TEACHER: "Их сургуулийн багш",
            PositionalCategory.UNIVERSITY_TEACHING_ASSISTANT: "Их сургуулийн багшийн туслах",
            PositionalCategory.UPHOLSTERER: "Эдлэлчин",
            PositionalCategory.USER_EXPERIENCE_EXPERT: "Хэрэглэгчийн туршлагын мэргэжилтэн",
            PositionalCategory.VAT_SPECIALIST: "НӨАТ-ийн мэргэжилтэн",
            PositionalCategory.VFX_ARTIST: "VFX уран бүтээлч",
            PositionalCategory.VARNISHER: "Лак түрхэгч",
            PositionalCategory.VEHICLE_BODY_REPAIRER: "Тээврийн хэрэгслийн бие засварч",
            PositionalCategory.VETERINARIAN: "Малын эмч",
            PositionalCategory.VETERINARY_TECHNICIAN: "Малын эмнэлгийн техникч",
            PositionalCategory.VISUAL_MERCHANDISER: "Визуал мерчандайзер",
            PositionalCategory.WAITER: "Зөөгч",
            PositionalCategory.WAITER_ROOM_SERVICE: "Зөөгч - Өрөөний үйлчилгээ",
            PositionalCategory.WARD_DOMESTIC: "Тасгийн гэрийн ажилтан",
            PositionalCategory.WARDROBE_ASSISTANT: "Хувцасны туслах",
            PositionalCategory.WAREHOUSE_MANAGER: "Агуулахын менежер",
            PositionalCategory.WAREHOUSEMAN: "Агуулахч",
            PositionalCategory.WATER_MANAGEMENT_ENGINEER: "Усны менежментийн инженер",
            PositionalCategory.WATER_MANAGEMENT_TECHNICIAN: "Усны менежментийн техникч",
            PositionalCategory.WEB_DESIGNER: "Веб дизайнер",
            PositionalCategory.WEBMASTER: "Вебмастер",
            PositionalCategory.WELDER: "Гагнуурч",
            PositionalCategory.WINDOW_DRESSER_DECORATOR: "Цонхны чимэглэгч",
            PositionalCategory.WOODWORKING_TECHNICIAN: "Модон эдлэлийн техникч",
            PositionalCategory.YOUTH_WORKER: "Залуучуудын ажилтан",
            PositionalCategory.IOS_DEVELOPER: "iOS хөгжүүлэгч",
            PositionalCategory.OTHER: "Бусад",
        }
        return names.get(self, self.value)


class JobClassificationInput(BaseModel):
    """Input data for job classification."""
    job_title: str = Field(..., description="The job title or position name")
    job_description: Optional[str] = Field(None, description="Full job description text")
    company_name: Optional[str] = Field(None, description="Company or organization name")
    additional_info: Optional[Any] = Field(None, description="Any additional relevant information")
    salary_min: Optional[int] = Field(None, description="Minimum salary offered for the position in MNT")
    salary_max: Optional[int] = Field(None, description="Maximum salary offered for the position in MNT")

class JobClassificationOutput(BaseModel):
    """Output data for job classification."""
    title: str = Field(..., description="Predicted job title")
    job_function: JobFunctionCategory = Field(..., description="Predicted job function category")
    job_industry: JobIndustryCategory = Field(..., description="Predicted job industry category")
    category: Category = Field(..., description="Predicted Paylab industry/sector category")
    positional_category: PositionalCategory = Field(..., description="Predicted Paylab positional/job title category")
    job_level: UnifiedJobLevelCategory = Field(..., description="Predicted unified job level category")
    salary_min: int= Field(..., description="Minimum salary in MNT based on classification input or estimation")
    salary_max: int = Field(..., description="Maximum salary in MNT based on classification input or estimation")
    experience_level: ExperienceLevel = Field(..., description="Predicted experience level category")
    education_level: EducationLevel = Field(..., description="Predicted education level category")
    company_name: Optional[str] = Field(None, description="Company or organization name if provided in input")
    requirement_reasoning: str = Field(..., description="Explanation of how the input data led to the predicted classifications. This should be 1 to 3 sentences in Mongolian language.")
    requirements: List[JobRequirement] = Field(default_factory=list, description="List of identified job requirements", min_length=0, max_length=5)
    benefits_reasoning: str = Field(..., description="Explanation of how the input data led to the identified benefits and bonuses. This should be 1 to 3 sentences in Mongolian language.")
    benefits: List[JobBenefit] = Field(default_factory=list, description="List of identified job benefits and bonuses", min_length=0, max_length=5)
    confidence_scores: Optional[dict[str, float]] = Field(None, description="Confidence scores for each predicted category")

class JobClassificationPaylabInput(BaseModel):
    """Input data for paylab agent to estimate salary based on job classification output."""
    category: Optional[Category] = Field(None, description="Paylab industry/sector category")
    positional_category: Optional[PositionalCategory] = Field(None, description="Paylab positional/job title category")
    category_min_salary: int = Field(..., description="Minimum salary in MNT for the predicted job category based on market data")
    category_max_salary: int = Field(..., description="Maximum salary in MNT for the predicted job category based on market data")
    title: str = Field(..., description="Predicted job title from classification output")
    salary_min: Optional[int] = Field(None, description="Minimum salary offered for the position in MNT if available")
    salary_max: Optional[int] = Field(None, description="Maximum salary offered for the position in MNT if available")

class JobClassificationPaylabOutput(BaseModel):
    """Output data for paylab agent's salary estimation."""
    salary_min: int = Field(..., description="Estimated minimum salary in MNT based on classification output and input salary information")
    salary_max: int = Field(..., description="Estimated maximum salary in MNT based on classification output and input salary information")
    justification: str = Field(..., description="Justification for the estimated salary range based on market data, industry standards, and specific job characteristics. This should be 1 to 3 sentences in Mongolian language.")

class JobClassifierAgentConfig(BaseModel):
    """Configuration for the Job Classification Agent."""
    system_prompt: str = Field(
         default=(
             "You are a high-precision job classification agent. "
             "Classify each job listing using this strict priority pipeline: Industry -> Function -> Level -> Techpack Category.\n"
             "Decision order rules:\n"
             "1) First decide Job Industry from strongest evidence (company domain, recruiter_industry, description).\n"
             "2) Then decide Job Function consistent with selected Industry and role duties.\n"
             "3) Then decide Unified Job Level from seniority/authority signals in title and responsibilities.\n"
             "4) Then decide Techpack Category, ensuring consistency with Function and Level.\n"
             "5) Then decide Experience Level and Education Level.\n"
             "Consistency rules:\n"
             "- Avoid OTHER unless evidence is genuinely unclear.\n"
             "- Function and Techpack must not contradict each other.\n"
             "- Executive titles must not be labeled as Staff/Specialist unless explicit evidence says otherwise.\n"
             "- Use provided enum values exactly.\n"
             "Extraction rules:\n"
             "- Extract up to 5 requirements and up to 5 benefits from the source text only.\n"
             "- Keep all reasoning and extracted text in Mongolian.\n"
             "Output rules:\n"
             "- Return valid JobClassificationOutput.\n"
             "- Always include short, evidence-based reasoning for requirement_reasoning and benefits_reasoning (1-3 sentences each).\n"
             "- For confidence_scores, include keys: job_industry, job_function, job_level, job_techpack_category, overall with values in [0,1].\n"
             "Batch mode: classify each listing independently and return one output per input in the same order."
            ),
        description="System prompt that guides the agent's behavior and response format."
    )
    system_paylab_prompt: str = Field(
        default=(
            "You are a compensation analyst agent. Based on the job classification output and salary input, provide a salary estimation and justification.\n"
            "1) If salary_min and salary_max are provided in the input, use them directly as the output without modification.\n"
            "2) If salary information is missing, estimate salary_min and salary_max based on the job classification output (job_function, job_industry, job_level, experience_level, education_level) and any salary signals in the job description.\n"
            "3) Provide a clear justification for the estimated salary range based on market data, industry standards, and the specific job characteristics. This should be 1-3 sentences in Mongolian."
            ),
        description="System prompt that guides the paylab agent's behavior and response format."
    )
    model_name: str = Field(default="google-gla:gemini-2.5-flash", description="Name of the language model to use for classification.")
    fallback_model_names: List[str] = Field(
        default_factory=lambda: ["google-gla:gemini-2.5-flash"],
        description="Fallback model names used when the primary model request fails."
    )
    max_batch_size: int = Field(
        default=50,
        ge=1,
        le=200,
        description="Maximum number of listings sent in one batch model request."
    )
    retry_attempts: int = Field(
        default=1,
        ge=0,
        le=5,
        description="Number of retries for failed model calls."
    )
    retry_backoff_seconds: float = Field(
        default=1.0,
        ge=0,
        le=30,
        description="Base backoff in seconds between retries."
    )



class JobClassifierAgent(Agent):
    """Agent for classifying job listings into various categories and extracting requirements and benefits."""
    config: JobClassifierAgentConfig
    def __init__(self, config: JobClassifierAgentConfig):
        self.config = config
        self.agent = Agent(model=self.config.model_name, system_prompt=self.config.system_prompt, output_type=JobClassificationOutput)
        self.batch_agent = Agent(model=self.config.model_name, system_prompt=self.config.system_prompt, output_type=List[JobClassificationOutput])
        self.paylab_agent = Agent(model=self.config.model_name, system_prompt=self.config.system_paylab_prompt, output_type=str)

    def _get_model_candidates(self) -> List[str]:
        candidates = [self.config.model_name, *self.config.fallback_model_names]
        # preserve order and remove duplicates
        uniq: list[str] = []
        for model in candidates:
            if model and model not in uniq:
                uniq.append(model)
        return uniq

    def _build_single_agent(self, model_name: str) -> Any:
        return Agent(model=model_name, system_prompt=self.config.system_prompt, output_type=JobClassificationOutput)

    def _build_batch_agent(self, model_name: str) -> Any:
        return Agent(model=model_name, system_prompt=self.config.system_prompt, output_type=List[JobClassificationOutput])

    def _build_paylab_agent(self, model_name: str) -> Any:
        return Agent(model=model_name, system_prompt=self.config.system_paylab_prompt, output_type=str)

    @staticmethod
    def _parse_paylab_json_output(raw_text: str) -> List[JobClassificationPaylabOutput]:
        payload_text = (raw_text or "").strip()
        if payload_text.startswith("```"):
            payload_text = payload_text.strip("`")
            if payload_text.lower().startswith("json"):
                payload_text = payload_text[4:].strip()

        payload = json.loads(payload_text)
        if not isinstance(payload, list):
            raise ValueError("Paylab output is not a JSON array.")

        parsed: List[JobClassificationPaylabOutput] = []
        for item in payload:
            if not isinstance(item, dict):
                raise ValueError("Paylab output item is not a JSON object.")
            parsed.append(
                JobClassificationPaylabOutput(
                    salary_min=int(item.get("salary_min", 0) or 0),
                    salary_max=int(item.get("salary_max", 0) or 0),
                    justification=str(item.get("justification", "") or "").strip(),
                )
            )
        return parsed

    @staticmethod
    def _normalize_text(text: str) -> str:
        cleaned = text.lower().replace("_", " ")
        cleaned = re.sub(r"\s+", " ", cleaned).strip()
        return cleaned

    def _match_industry_from_input(self, job_input: JobClassificationInput) -> Optional[JobIndustryCategory]:
        recruiter_industry = ""
        if isinstance(job_input.additional_info, dict):
            recruiter_industry = str(job_input.additional_info.get("recruiter_industry", "") or "")

        candidate_texts = [
            recruiter_industry,
            job_input.company_name or "",
            job_input.job_title or "",
            job_input.job_description or "",
        ]
        merged = self._normalize_text(" ".join(candidate_texts))
        recruiter_norm = self._normalize_text(recruiter_industry)

        if recruiter_norm:
            for industry in JobIndustryCategory:
                industry_norm = self._normalize_text(industry.value)
                if recruiter_norm == industry_norm or recruiter_norm in industry_norm or industry_norm in recruiter_norm:
                    return industry

        for industry in JobIndustryCategory:
            if industry == JobIndustryCategory.OTHER:
                continue
            industry_norm = self._normalize_text(industry.value)
            if industry_norm and industry_norm in merged:
                return industry

        return None

    def _infer_function_from_title(self, title: str) -> Optional[JobFunctionCategory]:
        title_norm = self._normalize_text(title)
        keyword_map: dict[JobFunctionCategory, list[str]] = {
            JobFunctionCategory.IT_TELECOM: ["developer", "software", "програм", "it", "систем", "ml", "data engineer", "devops", "qa", "security admin"],
            JobFunctionCategory.FINANCE_ACCOUNTING: ["санхүү", "нягтлан", "accountant", "finance", "cfo", "auditor", "эдийн засагч"],
            JobFunctionCategory.HR: ["хүний нөөц", "hr", "talent", "recruit"],
            JobFunctionCategory.MARKETING_PR: ["маркетинг", "brand", "pr", "контент", "social media"],
            JobFunctionCategory.SALES: ["борлуулалт", "sales", "account manager", "business sales"],
            JobFunctionCategory.BUSINESS_DEVELOPMENT: ["бизнес хөгжил", "business development", "partnership"],
            JobFunctionCategory.PROJECT_ALL: ["project manager", "төслийн", "pmo", "program manager"],
            JobFunctionCategory.ENGINEERING_TECHNICAL: ["инженер", "техник", "maintenance", "architect"],
            JobFunctionCategory.ADMINISTRATION: ["захиргаа", "office", "admin"],
            JobFunctionCategory.CUSTOMER_SERVICE: ["customer", "харилцагч", "call center", "support"],
            JobFunctionCategory.PROCUREMENT: ["худалдан авалт", "procurement", "sourcing", "buyer"],
            JobFunctionCategory.LEGAL: ["хууль", "legal", "compliance"],
            JobFunctionCategory.DISTRIBUTION_TRANSPORT: ["логистик", "тээвэр", "warehouse", "driver", "жолооч"],
            JobFunctionCategory.EXECUTIVE_MANAGEMENT: ["гүйцэтгэх захирал", "ceo", "general director", "ерөнхий захирал", "director"],
        }

        for function, keywords in keyword_map.items():
            if any(k in title_norm for k in keywords):
                return function
        return None

    def _infer_level_from_title(self, title: str) -> Optional[UnifiedJobLevelCategory]:
        title_norm = self._normalize_text(title)

        if any(k in title_norm for k in ["ceo", "гүйцэтгэх захирал", "chief", "ерөнхий захирал"]):
            return UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT
        if any(k in title_norm for k in ["захирал", "director", "head of", "албаны дарга"]):
            return UnifiedJobLevelCategory.SENIOR_MANAGEMENT
        if any(k in title_norm for k in ["менежер", "manager", "supervisor", "team lead", "ахлагч"]):
            return UnifiedJobLevelCategory.MIDDLE_MANAGEMENT
        if any(k in title_norm for k in ["senior", "ахлах", "principal", "lead "]):
            return UnifiedJobLevelCategory.SPECIALIST_SENIOR
        if any(k in title_norm for k in ["engineer", "developer", "analyst", "мэргэжилтэн", "инженер", "дизайнер", "нягтлан"]):
            return UnifiedJobLevelCategory.SPECIALIST
        if any(k in title_norm for k in ["ажилтан", "assistant", "оператор", "туслах", "жолооч", "касс"]):
            return UnifiedJobLevelCategory.STAFF

        return None

    def _match_positional_from_title(self, title: str) -> Optional[PositionalCategory]:
        title_norm = self._normalize_text(title)
        for cat in PositionalCategory:
            if cat == PositionalCategory.OTHER:
                continue
            if self._normalize_text(cat.value) == title_norm:
                return cat
            if self._normalize_text(cat.value) in title_norm:
                return cat
        return None

    def _build_classification_payload(self, job_input: JobClassificationInput) -> str:
        payload = {
            "classification_priority": ["job_industry", "job_function", "job_level", "category", "positional_category"],
            "job": job_input.model_dump(),
            "taxonomy": {
                "job_industry_values": [v.value for v in JobIndustryCategory],
                "job_function_values": [v.value for v in JobFunctionCategory],
                "job_level_values": [v.value for v in UnifiedJobLevelCategory],
                "category_values": [v.value for v in Category],
                "paylab_positional_values": [v.value for v in PositionalCategory],
                "experience_values": [v.value for v in ExperienceLevel],
                "education_values": [v.value for v in EducationLevel],
            },
        }
        return json.dumps(payload, ensure_ascii=False)

    def _refine_output(self, job_input: JobClassificationInput, output: JobClassificationOutput) -> JobClassificationOutput:
        title = job_input.job_title or output.title

        inferred_industry = self._match_industry_from_input(job_input)
        inferred_function = self._infer_function_from_title(title)
        inferred_level = self._infer_level_from_title(title)
        inferred_positional = self._match_positional_from_title(title)

        if inferred_industry and output.job_industry == JobIndustryCategory.OTHER:
            output.job_industry = inferred_industry

        if inferred_function and output.job_function == JobFunctionCategory.OTHER:
            output.job_function = inferred_function

        if inferred_level and output.job_level in {UnifiedJobLevelCategory.STAFF, UnifiedJobLevelCategory.SPECIALIST}:
            if inferred_level in {UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT, UnifiedJobLevelCategory.SENIOR_MANAGEMENT, UnifiedJobLevelCategory.MIDDLE_MANAGEMENT, UnifiedJobLevelCategory.SPECIALIST_SENIOR}:
                output.job_level = inferred_level

        if inferred_positional and output.positional_category == PositionalCategory.OTHER:
            output.positional_category = inferred_positional

        if output.job_function == JobFunctionCategory.EXECUTIVE_MANAGEMENT and output.job_level in {UnifiedJobLevelCategory.STAFF, UnifiedJobLevelCategory.SPECIALIST}:
            output.job_level = UnifiedJobLevelCategory.SENIOR_MANAGEMENT

        if output.job_level == UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT and output.job_function == JobFunctionCategory.OTHER:
            output.job_function = JobFunctionCategory.EXECUTIVE_MANAGEMENT

        if output.confidence_scores is None:
            output.confidence_scores = {}

        output.confidence_scores.setdefault("job_industry", 0.75 if inferred_industry else 0.6)
        output.confidence_scores.setdefault("job_function", 0.75 if inferred_function else 0.6)
        output.confidence_scores.setdefault("job_level", 0.75 if inferred_level else 0.6)
        output.confidence_scores.setdefault("positional_category", 0.75 if inferred_positional else 0.6)
        if "overall" not in output.confidence_scores:
            vals = [
                output.confidence_scores.get("job_industry", 0.6),
                output.confidence_scores.get("job_function", 0.6),
                output.confidence_scores.get("job_level", 0.6),
                output.confidence_scores.get("positional_category", 0.6),
            ]
            output.confidence_scores["overall"] = round(sum(vals) / len(vals), 3)

        return output

    async def _run_single_with_fallback(self, payload: str, job_input: JobClassificationInput) -> JobClassificationOutput:
        last_error: Optional[Exception] = None
        for model_name in self._get_model_candidates():
            agent = self._build_single_agent(model_name)
            for attempt in range(self.config.retry_attempts + 1):
                try:
                    response = await agent.run(payload)
                    print("Usage of model:", response.usage())
                    model_output = cast(JobClassificationOutput, response.output)
                    return self._refine_output(job_input, model_output)
                except Exception as exc:
                    last_error = exc
                    if attempt < self.config.retry_attempts:
                        await asyncio.sleep(self.config.retry_backoff_seconds * (attempt + 1))
                    else:
                        print(f"Single classification failed on model={model_name}: {exc}")

        if last_error is not None:
            raise last_error
        raise RuntimeError("Single classification failed for unknown reason.")

    async def _run_batch_chunk_with_fallback(self, job_inputs: List[JobClassificationInput]) -> List[JobClassificationOutput]:
        payloads = [self._build_classification_payload(item) for item in job_inputs]
        last_error: Optional[Exception] = None

        for model_name in self._get_model_candidates():
            agent = self._build_batch_agent(model_name)
            for attempt in range(self.config.retry_attempts + 1):
                try:
                    result = await agent.run(payloads)
                    print("Batch classification completed.")
                    print("Usage of model for batch classification:", result.usage())
                    batch_output = cast(List[JobClassificationOutput], result.output)
                    outputs: List[JobClassificationOutput] = []
                    for raw_input, classified in zip(job_inputs, batch_output):
                        outputs.append(self._refine_output(raw_input, classified))

                    if len(outputs) == len(job_inputs):
                        return outputs
                    raise RuntimeError(f"Batch output size mismatch. expected={len(job_inputs)} got={len(outputs)}")
                except Exception as exc:
                    last_error = exc
                    if attempt < self.config.retry_attempts:
                        await asyncio.sleep(self.config.retry_backoff_seconds * (attempt + 1))
                    else:
                        print(f"Batch chunk failed on model={model_name}: {exc}")

        # Fallback to single calls if all batch calls failed
        single_outputs: List[JobClassificationOutput] = []
        for item in job_inputs:
            payload = self._build_classification_payload(item)
            single_outputs.append(await self._run_single_with_fallback(payload, item))
        if len(single_outputs) == len(job_inputs):
            return single_outputs

        if last_error is not None:
            raise last_error
        raise RuntimeError("Batch classification failed for unknown reason.")

    async def classify_job(self, job_input: JobClassificationInput) -> JobClassificationOutput:
        """Classify a job listing and extract requirements and benefits."""
        payload = self._build_classification_payload(job_input)
        return await self._run_single_with_fallback(payload, job_input)
    
    async def classify_job_batch(self, job_inputs: List[JobClassificationInput]) -> List[JobClassificationOutput]:
        """Classify multiple job listings in batch."""
        print(f"Classifying batch of {len(job_inputs)} job listings...")
        outputs: List[JobClassificationOutput] = []
        step = self.config.max_batch_size
        for i in range(0, len(job_inputs), step):
            chunk = job_inputs[i:i + step]
            chunk_outputs = await self._run_batch_chunk_with_fallback(chunk)
            outputs.extend(chunk_outputs)
        print(f"Batch classification produced {len(outputs)} outputs.")
        return outputs
    
    async def paylab_job_batch(self, job_inputs: List[JobClassificationPaylabInput]) -> List[JobClassificationPaylabOutput]:
        """Run paylab agent to estimate salary for multiple job classifications in batch."""
        print(f"Running paylab agent for batch of {len(job_inputs)} job classifications...")
        inputs = ""
        for item in job_inputs:
            category_value = item.category.value if item.category is not None else "None"
            inputs += f"Category: {category_value}, Category Min Salary: {item.category_min_salary}, Category Max Salary: {item.category_max_salary}, Title: {item.title}, Salary Min: {item.salary_min}, Salary Max: {item.salary_max}\n"
        inputs += (
            "\nReturn ONLY a valid JSON array. "
            "Each item must have keys: salary_min (int), salary_max (int), justification (string). "
            "Do not include markdown, explanation, or extra keys. "
            "The output array length must exactly match the number of input rows in the same order."
        )
        
        last_error: Optional[Exception] = None
        for model_name in self._get_model_candidates():
            agent = self._build_paylab_agent(model_name)
            for attempt in range(self.config.retry_attempts + 1):
                try:
                    response = await agent.run(inputs)
                    print("Usage of model for paylab batch:", response.usage())
                    paylab_output = self._parse_paylab_json_output(cast(str, response.output))
                    if len(paylab_output) == len(job_inputs):
                        return paylab_output
                    raise RuntimeError(f"Paylab batch output size mismatch. expected={len(job_inputs)} got={len(paylab_output)}")
                except Exception as exc:
                    last_error = exc
                    if attempt < self.config.retry_attempts:
                        await asyncio.sleep(self.config.retry_backoff_seconds * (attempt + 1))
                    else:
                        print(f"Paylab batch failed on model={model_name}: {exc}")
        if last_error is not None:
            raise last_error
        raise RuntimeError("Paylab batch classification failed for unknown reason.")
