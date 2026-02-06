from __future__ import annotations

from enum import Enum
from typing import Any, List, Optional

from pydantic import BaseModel, Field
from pydantic_ai import Agent, BinaryContent


class JobLevelCategory(str, Enum):
    EXECUTIVE_MANAGEMENT = "Гүйцэтгэх удирдлага"
    MANAGEMENT = "Менежмент"
    SPECIALIST = "Мэргэжилтэн"
    STAFF = "Ажилтан"

    @property
    def description(self) -> str:
        descriptions = {
            JobLevelCategory.EXECUTIVE_MANAGEMENT: "Top-level executive management positions with organization-wide authority and strategic decision-making responsibility. These roles typically report to the board of directors, set company vision and direction, manage executive teams, and have full P&L accountability. Examples: CEO (Гүйцэтгэх захирал), CFO, COO, Executive Director. Corresponds to job grades 10-11. Requires extensive leadership experience (typically 15+ years) and proven track record of strategic management.",
            JobLevelCategory.MANAGEMENT: "Mid to senior-level management positions responsible for leading teams, departments, or business units. These roles involve people management, budget oversight, strategic planning within their domain, and cross-functional coordination. Managers make tactical decisions aligned with organizational strategy. Examples: Department Manager, Senior Manager, Unit Head, Functional Leadership. Corresponds to job grades 7-9. Typically requires 5-10+ years of experience with proven leadership capabilities.",
            JobLevelCategory.SPECIALIST: "Professional positions requiring specialized technical knowledge, expertise, or skills in a specific field or domain. These roles focus on executing specialized work, providing expert guidance, and solving complex problems within their area. May mentor junior staff but typically don't have formal management responsibilities. Examples: Senior Software Engineer, Financial Analyst, HR Specialist, Accountant. Corresponds to job grades 4-6. Requires university degree and 2-8 years of specialized experience.",
            JobLevelCategory.STAFF: "Entry-level, junior, or support positions that perform essential operational tasks and foundational work within the organization. These roles execute assigned tasks, follow established procedures, and support team objectives. Limited decision-making authority. Examples: Junior Employee, Assistant, Operator, Administrative Staff, Entry-level positions. Corresponds to job grades 1-3. May require high school to university education with 0-3 years of experience.",
        }
        return descriptions.get(self, "")


class JobGrade(str, Enum):
	LEVEL_1 = "1"
	LEVEL_2 = "2"
	LEVEL_3 = "3"
	LEVEL_4 = "4"
	LEVEL_5 = "5"
	LEVEL_6 = "6"
	LEVEL_7 = "7"
	LEVEL_8 = "8"
	LEVEL_9 = "9"
	LEVEL_10 = "10"
	LEVEL_11 = "11"


class JobLevel(str, Enum):
	"""Job position ladder/title for a given grade.
	NOTE: This enum represents the 'Албан тушаалын шатлал' column from the image.
	The numeric level is represented by `JobGrade`.
	"""

	EMPLOYEE = "Ажилтан"
	UNSKILLED_WORKER = "Мэргэжилгүй ажилтан"
	SKILLED_WORKER = "Мэргэжилтэй ажилтан"
	SPECIALIST = "Мэргэжилтэн"
	ADVANCED_SPECIALIST = "Ахисан түвшний мэргэжилтэн"
	SENIOR_SPECIALIST = "Ахлах мэргэжилтэн"
	MANAGER_SUPERVISOR = "Менежер / Супервайзор"
	SENIOR_MANAGER_UNIT_HEAD = "Ахлах менежер / Нэгжийн удирдлага"
	FUNCTIONAL_LEADERSHIP = "Чиг үүргийн удирдлага"
	DEPUTY_DIRECTOR = "Дэд захирал"
	CEO = "Гүйцэтгэх захирал"
	
	@property
	def description(self) -> str:
		descriptions = {
			JobLevel.EMPLOYEE: "Entry-level staff position (Ажилтан) requiring minimal to no formal education or experience. Performs basic operational tasks under direct supervision. Focuses on learning and executing simple, routine procedures. Grade Level 1. Examples: General laborer, office assistant, entry-level clerk.",
			JobLevel.UNSKILLED_WORKER: "Junior worker position (Мэргэжилгүй ажилтан) with basic operational responsibilities. May require high school education or vocational training. Performs routine tasks with some independence but still under supervision. Grade Level 2. Examples: Administrative assistant, data entry operator, junior technician.",
			JobLevel.SKILLED_WORKER: "Skilled worker position (Мэргэжилтэй ажилтан) requiring vocational certification, technical training, or some higher education. Performs specialized operational tasks independently with established procedures. 1-3 years experience typical. Grade Level 3. Examples: Skilled technician, junior accountant, experienced administrative staff.",
			JobLevel.SPECIALIST: "Professional specialist position (Мэргэжилтэн) requiring university degree and foundational expertise in a specific field. Works independently on professional-level tasks with moderate complexity. 2-4 years experience. Grade Level 4. Examples: Accountant, HR officer, software developer, analyst.",
			JobLevel.ADVANCED_SPECIALIST: "Advanced specialist position (Ахисан түвшний мэргэжилтэн) requiring university degree plus demonstrated advanced expertise. Handles complex problems, may lead small projects, provides guidance to junior staff. 4-6 years experience. Grade Level 5. Examples: Senior analyst, advanced engineer, specialized consultant.",
			JobLevel.SENIOR_SPECIALIST: "Senior specialist position (Ахлах мэргэжилтэн) requiring university degree and significant specialized experience. Subject matter expert who solves complex problems independently, mentors others, and may manage projects. 6-8+ years experience. Grade Level 6. Examples: Senior software engineer, senior financial analyst, senior specialist.",
			JobLevel.MANAGER_SUPERVISOR: "First-line management position (Менежер / Супервайзор) responsible for supervising a team or department. Manages day-to-day operations, people management, performance evaluation, and tactical execution. 5-7 years experience including team leadership. Grade Level 7. Examples: Team manager, department supervisor, project manager.",
			JobLevel.SENIOR_MANAGER_UNIT_HEAD: "Senior management position (Ахлах менежер / Нэгжийн удирдлага) leading a business unit, division, or large department. Responsible for strategic planning within scope, budget management, cross-functional coordination, and developing managers. 8-12 years experience. Grade Level 8. Examples: Department head, senior manager, division manager.",
			JobLevel.FUNCTIONAL_LEADERSHIP: "Functional leadership position (Чиг үүргийн удирдлага) managing major organizational functions, multiple departments, or critical business areas. Sets functional strategy, manages senior managers, represents function at executive level. 10-15 years experience. Grade Level 9. Examples: Director of Engineering, Head of Finance, Chief of Operations.",
			JobLevel.DEPUTY_DIRECTOR: "Deputy executive position (Дэд захирал) with organization-wide responsibilities. Supports CEO in overall company management, may oversee multiple functions, and has authority to make executive decisions. Second-in-command role. 12-18 years experience. Grade Level 10. Examples: Deputy CEO, Vice President, Deputy Director.",
			JobLevel.CEO: "Chief executive position (Гүйцэтгэх захирал) with ultimate responsibility for overall company leadership, vision, and performance. Reports to board of directors. Sets organizational strategy and culture. Highest decision-making authority. 15+ years experience including senior executive roles. Grade Level 11. Examples: CEO, Executive Director, General Director.",
		}
		return descriptions.get(self, "")


class JobCategory(str, Enum):
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
			JobCategory.CEO: "Chief Executive Officer (Гүйцэтгэх захирал) - The highest-ranking executive responsible for overall company strategy, vision, performance, and representing the organization to stakeholders. Makes final decisions on major company matters and reports to the board of directors.",
			JobCategory.DEPUTY_DIRECTOR: "Deputy Director (Дэд захирал) - Second-in-command executive who assists the CEO in overall company management, oversees multiple departments, and acts as CEO in their absence. Typically handles specific strategic initiatives or operational domains.",
			JobCategory.CFO: "Chief Financial Officer (Санхүү эрхэлсэн захирал) - Executive responsible for financial planning, risk management, financial reporting, treasury, and overall financial health of the organization. Oversees accounting, budgeting, and financial strategy.",
			JobCategory.GENERAL_ACCOUNTANT: "General Accountant (Ерөнхий нягтлан бодогч) - Senior accounting professional managing all accounting operations, financial reporting, ensuring compliance with regulations, overseeing bookkeeping, and coordinating with auditors.",
			JobCategory.ARCHITECTURE_DIRECTOR: "Architecture Director (Архитектур шийдэл хариуцсан захирал) - Executive responsible for enterprise architecture, technology strategy, system design principles, and ensuring technical solutions align with business goals. Typically in technology companies.",
			JobCategory.AGRICULTURE_TECH_DIRECTOR: "Agriculture Technology Director (Хөдөө аж ахуй хариуцсан технологийн захирал) - Director overseeing agricultural technology initiatives, agritech innovation, farming systems, and technology applications in agricultural sector.",
			JobCategory.MOBILE_DEVELOPER: "Mobile Developer (Мобайл хөгжүүлэгч) - Software developer specializing in creating mobile applications for iOS, Android, or cross-platform environments. Skills include Swift, Kotlin, Java, React Native, Flutter, etc.",
			JobCategory.SOFTWARE_ENGINEER: "Software Engineer (Программ хангамжийн инженер) - Professional who designs, develops, tests, and maintains software applications and systems. Works with programming languages, frameworks, and development methodologies.",
			JobCategory.SENIOR_SOFTWARE_DEVELOPER: "Senior Software Developer (Ахлах программ хөгжүүлэгч) - Experienced developer who leads technical design, mentors junior developers, makes architectural decisions, and delivers complex software solutions with high quality standards.",
			JobCategory.IT_SECURITY_ADMIN: "IT Security Administrator (Мэдээллийн аюулгүй байдал болон систем администрат) - Professional responsible for protecting IT infrastructure, implementing security policies, managing access controls, monitoring threats, and ensuring system security compliance.",
			JobCategory.PRODUCT_DESIGN_DIRECTOR: "Product Design Director (Бүтээгдэхүүний дизайн хариуцсан захирал) - Executive leading product design strategy, design teams, user experience vision, and ensuring design excellence across product portfolio.",
			JobCategory.PRODUCT_DESIGNER: "Product Designer (Бүтээгдэхүүн хариуцсан дизайнер) - Designer who creates user interfaces, user experiences, and product designs. Conducts user research, creates wireframes, prototypes, and visual designs for digital or physical products.",
			JobCategory.SENIOR_PRODUCT_DESIGNER: "Senior Product Designer (Бүтээгдэхүүн хариуцсан ахлах дизайнер) - Experienced designer who leads design projects, establishes design systems, mentors junior designers, and drives design strategy for complex products.",
			JobCategory.SENIOR_HR_OFFICER: "Senior HR Officer (Хүний нөөцийн ахлах ажилтан) - Senior human resources professional managing recruitment, employee relations, performance management, benefits administration, and HR policy implementation.",
			JobCategory.HR_OFFICER: "HR Officer (Хүний нөөцийн ажилтан) - Human resources professional handling recruitment processes, onboarding, employee records, basic employee relations, and supporting HR operations.",
			JobCategory.ADMIN_OFFICER: "Administrative Officer (Захиргааны ажилтан) - Professional providing administrative support including office management, documentation, scheduling, coordination, and general operational assistance.",
			JobCategory.PROJECT_MANAGEMENT_HEAD: "Project Management Head (Төслийн удирдлагын албаны дарга) - Director or head of the project management office (PMO), responsible for organizational project management standards, methodologies, and portfolio oversight.",
			JobCategory.PROJECT_MANAGEMENT_OFFICER: "Project Management Officer (Төслийн удирдлагын ажилтан) - Professional supporting project management activities, maintaining project documentation, coordinating resources, tracking progress, and ensuring PMO standards compliance.",
			JobCategory.PROJECT_MANAGER: "Project Manager (Төслийн менежер) - Professional responsible for planning, executing, and closing projects. Manages scope, timeline, budget, resources, stakeholders, and ensures successful project delivery.",
			JobCategory.PROGRAMMER: "Programmer (Програмист) - Developer who writes, tests, and maintains code. Implements software solutions based on specifications using programming languages and development tools.",
			JobCategory.SENIOR_PROGRAMMER: "Senior Programmer (Ахлах програмист) - Experienced programmer who handles complex coding challenges, reviews code, mentors junior programmers, and ensures code quality and best practices.",
			JobCategory.SYSTEM_DEVELOPER: "System Developer (Систем хөгжүүлэгч) - Developer specializing in building and maintaining system-level software, backend systems, databases, and enterprise applications.",
			JobCategory.MULTIMEDIA_DESIGNER: "Multimedia Designer (Мультимедиа дизайнер) - Creative professional designing visual and audio content including graphics, animations, videos, and interactive media for various platforms.",
			JobCategory.MACHINE_LEARNING_ENGINEER: "Machine Learning Engineer (Машин сургалтын инженер) - Engineer who develops, implements, and deploys machine learning models and AI systems. Works with data, algorithms, ML frameworks, and model optimization.",
			JobCategory.BUSINESS_DEVELOPMENT_MANAGER: "Business Development Manager (Бизнес хөгжлийн менежер) - Professional responsible for identifying growth opportunities, building partnerships, driving sales strategy, and expanding business reach.",
			JobCategory.SENIOR_MACHINE_LEARNING_ENGINEER: "Senior Machine Learning Engineer (Ахлах машин сургалтын инженер) - Experienced ML engineer leading AI/ML initiatives, designing complex models, establishing ML infrastructure, and mentoring ML teams.",
			JobCategory.SENIOR_DATA_ENGINEER: "Senior Data Engineer (Ахлах дата инженер) - Experienced engineer who designs and maintains data infrastructure, pipelines, warehouses, and ensures data quality, availability, and performance at scale.",
			JobCategory.HEALTH_TECH_DIRECTOR: "Health Technology Director (Эрүүл мэндийн салбар хариуцсан технологийн захирал) - Director overseeing health technology initiatives, medical technology systems, healthtech innovation, and technology applications in healthcare sector.",
			JobCategory.FINANCIAL_ANALYST: "Financial Analyst (Санхүүгийн шинжээч) - Professional who analyzes financial data, creates reports, develops forecasts, evaluates investments, and provides insights to support business decisions.",
			JobCategory.OTHER: "Other (Бусад) - Job categories that don't fit the predefined classifications. Use this for unique, rare, or cross-functional roles not covered by specific categories.",
		}
		return descriptions.get(self, "")

#Хангамж / Урамшуулал
class JobBonus(BaseModel):
	name: Optional[str] = Field(None, description="The name or title of the bonus or benefit offered. Examples: 'Performance Bonus', 'Meal Allowance', 'Transportation Benefit', 'Health Insurance', 'Annual Leave', 'Stock Options', etc. Use the exact terminology mentioned in the job posting when possible. If multiple bonuses are mentioned, list each one separately with its specific name. Make it clear and must be in english")
	description: Optional[str] = Field(None, description="Detailed information about the bonus or benefit, including conditions, amounts, frequency, eligibility criteria, or any specific details mentioned in the job posting. Be comprehensive and include all relevant information provided. Its new should be null make it just empty text. Make it clear and must be in mongolian")

class Requirements(BaseModel):
	name: Optional[str] = Field(None, description="The category or type of requirement. Examples: 'Education', 'Work Experience', 'Technical Skills', 'Language Proficiency', 'Certifications', 'Soft Skills', 'Physical Requirements', 'Age Range', 'Driver's License', 'Software Proficiency', etc. Use clear, standardized category names. If multiple requirements are mentioned, list each one separately with its specific category. Result must be in mongolian")
	details: Optional[str] = Field(None, description="The specific requirement details and criteria. Include exact qualifications such as degree level, years of experience, specific programming languages, proficiency levels, certification names, or any other detailed prerequisites. Extract verbatim when possible and include whether it's mandatory or preferred. Make it clear and must be in mongolian")


class JobClasifyOutput(BaseModel):
	name: Optional[str] = Field(None, description="The official job title or position name as listed in the job posting. Extract the exact title without modifications.")
	company: Optional[str] = Field(None, description="The full legal name or brand name of the company or organization offering the position. Use the Mongolian name if available, otherwise use English.")
	min_salary: Optional[int] = Field(None, description="The minimum salary amount offered for this position in Mongolian Tugrik (MNT). Extract only if explicitly stated. Use null if salary is negotiable or not mentioned.")
	max_salary: Optional[int] = Field(None, description="The maximum salary amount offered for this position in Mongolian Tugrik (MNT). Extract only if explicitly stated. Use null if salary is negotiable or not mentioned.")
	bonus: Optional[List[JobBonus]] = Field(None, description="A comprehensive list of all additional compensation, bonuses, benefits, and incentives mentioned in the job posting. Include performance bonuses, meal allowances, transportation benefits, insurance, vacation days, stock options, etc. Extract as many details as possible.")
	requirements: Optional[List[Requirements]] = Field(None, description="All qualifications, skills, experience levels, education requirements, certifications, language proficiencies, and other prerequisites mentioned for the position. Be thorough and include both mandatory and preferred requirements.")
	job_level_category: Optional[JobLevelCategory] = Field(None, description="The broad organizational hierarchy category this position belongs to. Determine based on: EXECUTIVE_MANAGEMENT (CEO, CFO level 10-11), MANAGEMENT (Manager, Senior Manager level 7-9), SPECIALIST (professional requiring degree level 4-6), or STAFF (entry-level or support level 1-3). Analyze the job title, responsibilities, and required experience to classify correctly.")
	job_grade: Optional[JobGrade] = Field(None, description="The numerical grade level from 1 to 11 representing the position's rank in the organizational hierarchy. Level 1-3: entry-level staff, Level 4-6: specialists and professionals, Level 7-9: management positions, Level 10-11: executive leadership. Consider job responsibilities, required experience, and decision-making authority.")
	job_level: Optional[JobLevel] = Field(None, description="The specific Mongolian job level title that best matches this position. Choose from the predefined enum values based on the position's requirements and responsibilities. Consider education requirements, experience level, and scope of authority to determine the appropriate level title.")
	job_category: Optional[JobCategory] = Field(None, description="The specific functional role or job category that best describes this position. Select from the predefined enum values based on the primary job function, technical skills required, and industry context. If no exact match exists, use OTHER. Consider the core responsibilities and technical domain of the role.")


class TechpackJobClasifierConfig(BaseModel):
	system_prompt: str = Field(default="You are an expert job market analyst specializing in Mongolian job market data classification.", description="System prompt for the analysis model")
	model_name: str = Field(default="google-gla:gemini-3-pro-preview", description="Model name to use for analysis")

class TechpackJobClasifierAgent:
	config: TechpackJobClasifierConfig
	def __init__(self, config: TechpackJobClasifierConfig):
		self.config = config	
		self.agent = Agent(
			self.config.model_name,
			system_prompt=self.config.system_prompt,
			output_type=JobClasifyOutput
		)
		self.batch_agent = Agent(
			self.config.model_name,
			system_prompt=self.config.system_prompt,
			output_type=List[JobClasifyOutput]
		)

	async def classify_job(self, input_data: dict):
		"""Classify a single job description."""
		input = str(input_data)
		try:
			response = await self.agent.run(input)
			return response.output
		except Exception as e:
			print(f"Error classifying job: {e}")
			return None

	async def classify_job_batch(self, input_data: List[dict], batch_size: int = 100):
		"""Classify jobs using batch_agent (100 jobs per batch) with 10 parallel batches."""
		import asyncio
		all_results = []
		total = len(input_data)
		
		# Process 15 batches in parallel (each batch processes 100 jobs)
		parallel_batches = 10
		chunk_size = batch_size * parallel_batches  # 2000 jobs at a time
		
		for chunk_start in range(0, total, chunk_size):
			# Create up to 10 parallel tasks
			tasks = []
			for i in range(parallel_batches):
				batch_start = chunk_start + (i * batch_size)
				if batch_start >= total:
					break
				
				batch = input_data[batch_start:batch_start + batch_size]
				if batch:
					print(f"Preparing batch {batch_start // batch_size + 1} with {len(batch)} jobs")
					tasks.append(self.batch_agent.run(str(batch)))
			
			if tasks:
				print(f"Running {len(tasks)} batches in parallel...")
				# Execute all tasks in parallel
				results = await asyncio.gather(*tasks, return_exceptions=True)
				try:
					# Collect results
					for result in results:
						if isinstance(result, Exception):
							print(f"Error in batch: {result}")
						elif result is not None and hasattr(result, 'data'):
							all_results.extend(result.data) # type: ignore
				except Exception as e:
					print(f"Error processing batch results: {e}")
		print(f"Total jobs processed: {len(all_results)}")
		return all_results
	

class JobSalaryRequirement(BaseModel):
	name: str = Field(..., description="The category or type of requirement related to salary calculation. Examples: 'Experience Level', 'Education Level', 'Skills Required', 'Certifications', 'Job Location', etc. Use clear, standardized category names. If multiple requirements are mentioned, list each one separately with its specific category. Must be in mongolian")
	details: str = Field(..., description="The specific requirement details and criteria that impact salary. Include exact qualifications such as years of experience, degree level, specific skills, certification names, or any other detailed prerequisites relevant to salary determination. Must be in mongolian")

class JobSalaryBonus(BaseModel):
	name: str = Field(..., description="The name or title of the bonus or benefit that influences salary. Examples: 'Performance Bonus', 'Overtime Pay', 'Shift Allowance', etc. Use the exact terminology mentioned in the job posting when possible. Must be in mongolian")
	description: str = Field(..., description="Detailed information about how the bonus or benefit affects salary, including conditions, amounts, frequency, eligibility criteria, or any specific details mentioned in the job posting. Must be in mongolian")


class JobSalaryOutput(BaseModel):
	min_salary: int = Field(..., description="The calculated minimum salary amount for this position in Mongolian Tugrik (MNT).")
	max_salary: int= Field(..., description="The calculated maximum salary amount for this position in Mongolian Tugrik (MNT).")
	average_salary: int = Field(..., description="The calculated median salary amount for this position in Mongolian Tugrik (MNT).")
	requirements_details: str = Field(..., description="A detailed explanation of how various job requirements impact the salary calculation for this position. That should be selected")
	requirements: List[JobSalaryRequirement] = Field(..., description="A list of specific requirements that impact the salary calculation for this position. That should be max 5 requirements.", max_length=5, min_length=1)
	bonus_details: str = Field(..., description="A detailed explanation of how various bonuses or benefits influence the salary calculation for this position.")
	bonus: List[JobSalaryBonus] = Field(..., description="A list of bonuses or benefits that influence the salary calculation for this position. That should be max 5 bonuses.", max_length=5, min_length=1)

class TechpackJobSalaryCalculatorConfig(BaseModel):
	system_prompt: str = Field(default="You are an expert job market analyst specializing in Mongolian job market salary analysis.", description="System prompt for the salary analysis model")
	model_name: str = Field(default="google-gla:gemini-3-pro-preview", description="Model name to use for salary analysis")

class TechpackJobSalaryCalculatorAgent:
	config: TechpackJobSalaryCalculatorConfig
	def __init__(self, config: TechpackJobSalaryCalculatorConfig):
		self.config = config	
		self.agent = Agent(
			model=self.config.model_name,
			system_prompt=self.config.system_prompt,
			output_type=JobSalaryOutput
		)
	async def calculate_salary(self, input_data: str | BinaryContent | List[BinaryContent]):
		"""Calculate salary for a single job description."""
		try:
			if isinstance(input_data, BinaryContent):
				response = await self.agent.run([input_data])
			else:
				response = await self.agent.run(input_data)
			return response.output
		except Exception as e:
			print(f"Error calculating salary: {e}")
			return None