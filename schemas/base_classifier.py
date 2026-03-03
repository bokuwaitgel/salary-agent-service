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
    EXECUTIVE_MANAGEMENT = "Гүйцэтгэх удирдлага"  # CEO, Deputy Directors
    SENIOR_MANAGEMENT = "Ахлах удирдлага"  # Directors, Senior Managers
    MIDDLE_MANAGEMENT = "Дунд удирдлага"  # Managers, Department Heads
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
                "Mid-level management (Managers, Team Leads, Supervisors). Job grades 6-7. "
                "Manages teams/departments, tactical execution, people management, budget oversight. "
                "Requires 5-10 years experience with leadership capabilities.",
            
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
            UnifiedJobLevelCategory.MIDDLE_MANAGEMENT: 1.8,
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

class JobTechpackCategory(str, Enum):
	CEO = "Гүйцэтгэх захирал"
	DEPUTY_DIRECTOR = "Дэд захирал"
	CFO = "Санхүү эрхэлсэн захирал"
	GENERAL_ACCOUNTANT = "Ерөнхий нягтлан бодогч"
	ARCHITECTURE_DIRECTOR = "Архитектур шийдэл хариуцсан захирал"
	AGRICULTURE_TECH_DIRECTOR = "Хөдөө аж ахуй хариуцсан технологийн захирал"
	MOBILE_DEVELOPER = "Мобайл хөгжүүлэгч"
	SOFTWARE_ENGINEER = "Программ хангамжийн инженер"
	SENIOR_SOFTWARE_DEVELOPER = "Ахлах программ хөгжүүлэгч"
	IT_SECURITY_ADMIN = "Мэдээллийн аюулгүй байдал болон систем администрат"
	PRODUCT_DESIGN_DIRECTOR = "Бүтээгдэхүүний дизайн хариуцсан захирал"
	PRODUCT_DESIGNER = "Бүтээгдэхүүн хариуцсан дизайнер"
	SENIOR_PRODUCT_DESIGNER = "Бүтээгдэхүүн хариуцсан ахлах дизайнер"
	SENIOR_HR_OFFICER = "Хүний нөөцийн ахлах ажилтан"
	HR_OFFICER = "Хүний нөөцийн ажилтан"
	ADMIN_OFFICER = "Захиргааны ажилтан"
	PROJECT_MANAGEMENT_HEAD = "Төслийн удирдлагын албаны дарга"
	PROJECT_MANAGEMENT_OFFICER = "Төслийн удирдлагын ажилтан"
	PROJECT_MANAGER = "Төслийн менежер"
	PROGRAMMER = "Програмист"
	SENIOR_PROGRAMMER = "Ахлах програмист"
	SYSTEM_DEVELOPER = "Систем хөгжүүлэгч"
	MULTIMEDIA_DESIGNER = "Мультимедиа дизайнер"
	MACHINE_LEARNING_ENGINEER = "Машин сургалтын инженер"
	BUSINESS_DEVELOPMENT_MANAGER = "Бизнес хөгжлийн менежер"
	SENIOR_MACHINE_LEARNING_ENGINEER = "Ахлах машин сургалтын инженер"
	SENIOR_DATA_ENGINEER = "Ахлах дата инженер"
	HEALTH_TECH_DIRECTOR = "Эрүүл мэндийн салбар хариуцсан технологийн захирал"
	FINANCIAL_ANALYST = "Санхүүгийн шинжээч"
	# Add more job categories as needed
	OTHER = "Бусад"

	@property
	def description(self) -> str:
		descriptions = {
			JobTechpackCategory.CEO: "Chief Executive Officer (Гүйцэтгэх захирал) - The highest-ranking executive responsible for overall company strategy, vision, performance, and representing the organization to stakeholders. Makes final decisions on major company matters and reports to the board of directors.",
			JobTechpackCategory.DEPUTY_DIRECTOR: "Deputy Director (Дэд захирал) - Second-in-command executive who assists the CEO in overall company management, oversees multiple departments, and acts as CEO in their absence. Typically handles specific strategic initiatives or operational domains.",
			JobTechpackCategory.CFO: "Chief Financial Officer (Санхүү эрхэлсэн захирал) - Executive responsible for financial planning, risk management, financial reporting, treasury, and overall financial health of the organization. Oversees accounting, budgeting, and financial strategy.",
			JobTechpackCategory.GENERAL_ACCOUNTANT: "General Accountant (Ерөнхий нягтлан бодогч) - Senior accounting professional managing all accounting operations, financial reporting, ensuring compliance with regulations, overseeing bookkeeping, and coordinating with auditors.",
			JobTechpackCategory.ARCHITECTURE_DIRECTOR: "Architecture Director (Архитектур шийдэл хариуцсан захирал) - Executive responsible for enterprise architecture, technology strategy, system design principles, and ensuring technical solutions align with business goals. Typically in technology companies.",
			JobTechpackCategory.AGRICULTURE_TECH_DIRECTOR: "Agriculture Technology Director (Хөдөө аж ахуй хариуцсан технологийн захирал) - Director overseeing agricultural technology initiatives, agritech innovation, farming systems, and technology applications in agricultural sector.",
			JobTechpackCategory.MOBILE_DEVELOPER: "Mobile Developer (Мобайл хөгжүүлэгч) - Software developer specializing in creating mobile applications for iOS, Android, or cross-platform environments. Skills include Swift, Kotlin, Java, React Native, Flutter, etc.",
			JobTechpackCategory.SOFTWARE_ENGINEER: "Software Engineer (Программ хангамжийн инженер) - Professional who designs, develops, tests, and maintains software applications and systems. Works with programming languages, frameworks, and development methodologies.",
			JobTechpackCategory.SENIOR_SOFTWARE_DEVELOPER: "Senior Software Developer (Ахлах программ хөгжүүлэгч) - Experienced developer who leads technical design, mentors junior developers, makes architectural decisions, and delivers complex software solutions with high quality standards.",
			JobTechpackCategory.IT_SECURITY_ADMIN: "IT Security Administrator (Мэдээллийн аюулгүй байдал болон систем администрат) - Professional responsible for protecting IT infrastructure, implementing security policies, managing access controls, monitoring threats, and ensuring system security compliance.",
			JobTechpackCategory.PRODUCT_DESIGN_DIRECTOR: "Product Design Director (Бүтээгдэхүүний дизайн хариуцсан захирал) - Executive leading product design strategy, design teams, user experience vision, and ensuring design excellence across product portfolio.",
			JobTechpackCategory.PRODUCT_DESIGNER: "Product Designer (Бүтээгдэхүүн хариуцсан дизайнер) - Designer who creates user interfaces, user experiences, and product designs. Conducts user research, creates wireframes, prototypes, and visual designs for digital or physical products.",
			JobTechpackCategory.SENIOR_PRODUCT_DESIGNER: "Senior Product Designer (Бүтээгдэхүүн хариуцсан ахлах дизайнер) - Experienced designer who leads design projects, establishes design systems, mentors junior designers, and drives design strategy for complex products.",
			JobTechpackCategory.SENIOR_HR_OFFICER: "Senior HR Officer (Хүний нөөцийн ахлах ажилтан) - Senior human resources professional managing recruitment, employee relations, performance management, benefits administration, and HR policy implementation.",
			JobTechpackCategory.HR_OFFICER: "HR Officer (Хүний нөөцийн ажилтан) - Human resources professional handling recruitment processes, onboarding, employee records, basic employee relations, and supporting HR operations.",
			JobTechpackCategory.ADMIN_OFFICER: "Administrative Officer (Захиргааны ажилтан) - Professional providing administrative support including office management, documentation, scheduling, coordination, and general operational assistance.",
			JobTechpackCategory.PROJECT_MANAGEMENT_HEAD: "Project Management Head (Төслийн удирдлагын албаны дарга) - Director or head of the project management office (PMO), responsible for organizational project management standards, methodologies, and portfolio oversight.",
			JobTechpackCategory.PROJECT_MANAGEMENT_OFFICER: "Project Management Officer (Төслийн удирдлагын ажилтан) - Professional supporting project management activities, maintaining project documentation, coordinating resources, tracking progress, and ensuring PMO standards compliance.",
			JobTechpackCategory.PROJECT_MANAGER: "Project Manager (Төслийн менежер) - Professional responsible for planning, executing, and closing projects. Manages scope, timeline, budget, resources, stakeholders, and ensures successful project delivery.",
			JobTechpackCategory.PROGRAMMER: "Programmer (Програмист) - Developer who writes, tests, and maintains code. Implements software solutions based on specifications using programming languages and development tools.",
			JobTechpackCategory.SENIOR_PROGRAMMER: "Senior Programmer (Ахлах програмист) - Experienced programmer who handles complex coding challenges, reviews code, mentors junior programmers, and ensures code quality and best practices.",
			JobTechpackCategory.SYSTEM_DEVELOPER: "System Developer (Систем хөгжүүлэгч) - Developer specializing in building and maintaining system-level software, backend systems, databases, and enterprise applications.",
			JobTechpackCategory.MULTIMEDIA_DESIGNER: "Multimedia Designer (Мультимедиа дизайнер) - Creative professional designing visual and audio content including graphics, animations, videos, and interactive media for various platforms.",
			JobTechpackCategory.MACHINE_LEARNING_ENGINEER: "Machine Learning Engineer (Машин сургалтын инженер) - Engineer who develops, implements, and deploys machine learning models and AI systems. Works with data, algorithms, ML frameworks, and model optimization.",
			JobTechpackCategory.BUSINESS_DEVELOPMENT_MANAGER: "Business Development Manager (Бизнес хөгжлийн менежер) - Professional responsible for identifying growth opportunities, building partnerships, driving sales strategy, and expanding business reach.",
			JobTechpackCategory.SENIOR_MACHINE_LEARNING_ENGINEER: "Senior Machine Learning Engineer (Ахлах машин сургалтын инженер) - Experienced ML engineer leading AI/ML initiatives, designing complex models, establishing ML infrastructure, and mentoring ML teams.",
			JobTechpackCategory.SENIOR_DATA_ENGINEER: "Senior Data Engineer (Ахлах дата инженер) - Experienced engineer who designs and maintains data infrastructure, pipelines, warehouses, and ensures data quality, availability, and performance at scale.",
			JobTechpackCategory.HEALTH_TECH_DIRECTOR: "Health Technology Director (Эрүүл мэндийн салбар хариуцсан технологийн захирал) - Director overseeing health technology initiatives, medical technology systems, healthtech innovation, and technology applications in healthcare sector.",
			JobTechpackCategory.FINANCIAL_ANALYST: "Financial Analyst (Санхүүгийн шинжээч) - Professional who analyzes financial data, creates reports, develops forecasts, evaluates investments, and provides insights to support business decisions.",
			JobTechpackCategory.OTHER: "Other (Бусад) - Job categories that don't fit the predefined classifications. Use this for unique, rare, or cross-functional roles not covered by specific categories.",
		}
		return descriptions.get(self, "")
    

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
    job_techpack_category: JobTechpackCategory = Field(..., description="Predicted job category based on techpack classification")
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
    model_name: str = Field(default="google-gla:gemini-2.5-pro", description="Name of the language model to use for classification.")
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

    def _match_techpack_from_title(self, title: str) -> Optional[JobTechpackCategory]:
        title_norm = self._normalize_text(title)
        for category in JobTechpackCategory:
            if category == JobTechpackCategory.OTHER:
                continue
            if self._normalize_text(category.value) == title_norm:
                return category
            if self._normalize_text(category.value) in title_norm:
                return category
        return None

    def _build_classification_payload(self, job_input: JobClassificationInput) -> str:
        payload = {
            "classification_priority": ["job_industry", "job_function", "job_level", "job_techpack_category"],
            "job": job_input.model_dump(),
            "taxonomy": {
                "job_industry_values": [v.value for v in JobIndustryCategory],
                "job_function_values": [v.value for v in JobFunctionCategory],
                "job_level_values": [v.value for v in UnifiedJobLevelCategory],
                "job_techpack_values": [v.value for v in JobTechpackCategory],
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
        inferred_techpack = self._match_techpack_from_title(title)

        if inferred_industry and output.job_industry == JobIndustryCategory.OTHER:
            output.job_industry = inferred_industry

        if inferred_function and output.job_function == JobFunctionCategory.OTHER:
            output.job_function = inferred_function

        if inferred_level and output.job_level in {UnifiedJobLevelCategory.STAFF, UnifiedJobLevelCategory.SPECIALIST}:
            if inferred_level in {UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT, UnifiedJobLevelCategory.SENIOR_MANAGEMENT, UnifiedJobLevelCategory.MIDDLE_MANAGEMENT, UnifiedJobLevelCategory.SPECIALIST_SENIOR}:
                output.job_level = inferred_level

        if inferred_techpack and output.job_techpack_category == JobTechpackCategory.OTHER:
            output.job_techpack_category = inferred_techpack

        techpack_consistency_map: dict[JobTechpackCategory, tuple[JobFunctionCategory, UnifiedJobLevelCategory]] = {
            JobTechpackCategory.CEO: (JobFunctionCategory.EXECUTIVE_MANAGEMENT, UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT),
            JobTechpackCategory.DEPUTY_DIRECTOR: (JobFunctionCategory.EXECUTIVE_MANAGEMENT, UnifiedJobLevelCategory.SENIOR_MANAGEMENT),
            JobTechpackCategory.CFO: (JobFunctionCategory.FINANCE_ACCOUNTING, UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT),
            JobTechpackCategory.ARCHITECTURE_DIRECTOR: (JobFunctionCategory.IT_TELECOM, UnifiedJobLevelCategory.SENIOR_MANAGEMENT),
            JobTechpackCategory.AGRICULTURE_TECH_DIRECTOR: (JobFunctionCategory.ENGINEERING_TECHNICAL, UnifiedJobLevelCategory.SENIOR_MANAGEMENT),
            JobTechpackCategory.PRODUCT_DESIGN_DIRECTOR: (JobFunctionCategory.CONTENT_DESIGN, UnifiedJobLevelCategory.SENIOR_MANAGEMENT),
            JobTechpackCategory.HEALTH_TECH_DIRECTOR: (JobFunctionCategory.HEALTHCARE, UnifiedJobLevelCategory.SENIOR_MANAGEMENT),
            JobTechpackCategory.GENERAL_ACCOUNTANT: (JobFunctionCategory.FINANCE_ACCOUNTING, UnifiedJobLevelCategory.SPECIALIST_SENIOR),
            JobTechpackCategory.SENIOR_SOFTWARE_DEVELOPER: (JobFunctionCategory.IT_TELECOM, UnifiedJobLevelCategory.SPECIALIST_SENIOR),
            JobTechpackCategory.SENIOR_PROGRAMMER: (JobFunctionCategory.IT_TELECOM, UnifiedJobLevelCategory.SPECIALIST_SENIOR),
            JobTechpackCategory.SENIOR_MACHINE_LEARNING_ENGINEER: (JobFunctionCategory.IT_TELECOM, UnifiedJobLevelCategory.SPECIALIST_SENIOR),
            JobTechpackCategory.SENIOR_DATA_ENGINEER: (JobFunctionCategory.IT_TELECOM, UnifiedJobLevelCategory.SPECIALIST_SENIOR),
        }

        if output.job_techpack_category in techpack_consistency_map:
            expected_function, expected_level = techpack_consistency_map[output.job_techpack_category]
            if output.job_function in {JobFunctionCategory.OTHER, JobFunctionCategory.EXECUTIVE_MANAGEMENT, JobFunctionCategory.IT_TELECOM, JobFunctionCategory.FINANCE_ACCOUNTING, JobFunctionCategory.CONTENT_DESIGN, JobFunctionCategory.ENGINEERING_TECHNICAL, JobFunctionCategory.HEALTHCARE}:
                output.job_function = expected_function
            if output.job_level in {UnifiedJobLevelCategory.STAFF, UnifiedJobLevelCategory.SPECIALIST, UnifiedJobLevelCategory.MIDDLE_MANAGEMENT, UnifiedJobLevelCategory.SENIOR_MANAGEMENT, UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT}:
                # always enforce minimum expected level for known techpack category
                output.job_level = expected_level

        if output.job_function == JobFunctionCategory.EXECUTIVE_MANAGEMENT and output.job_level in {UnifiedJobLevelCategory.STAFF, UnifiedJobLevelCategory.SPECIALIST}:
            output.job_level = UnifiedJobLevelCategory.SENIOR_MANAGEMENT

        if output.job_level == UnifiedJobLevelCategory.EXECUTIVE_MANAGEMENT and output.job_function == JobFunctionCategory.OTHER:
            output.job_function = JobFunctionCategory.EXECUTIVE_MANAGEMENT

        if output.confidence_scores is None:
            output.confidence_scores = {}

        output.confidence_scores.setdefault("job_industry", 0.75 if inferred_industry else 0.6)
        output.confidence_scores.setdefault("job_function", 0.75 if inferred_function else 0.6)
        output.confidence_scores.setdefault("job_level", 0.75 if inferred_level else 0.6)
        output.confidence_scores.setdefault("job_techpack_category", 0.75 if inferred_techpack else 0.6)
        if "overall" not in output.confidence_scores:
            vals = [
                output.confidence_scores.get("job_industry", 0.6),
                output.confidence_scores.get("job_function", 0.6),
                output.confidence_scores.get("job_level", 0.6),
                output.confidence_scores.get("job_techpack_category", 0.6),
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



