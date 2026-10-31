"""
Opportunity & Visa Matcher — LlamaIndex RAG Engine

Evaluates candidate CVs against opportunity specifications and cross-references
live immigration and visa regulations to produce detailed eligibility reports.
"""

import os
from typing import List, Optional
from dotenv import load_dotenv
import html2text
from pypdf import PdfReader
import requests

from llama_index.core import Document, Settings, VectorStoreIndex
from llama_index.embeddings.gemini import GeminiEmbedding
from llama_index.llms.gemini import Gemini

load_dotenv()

GEMINI_MODEL = "models/gemini-3.5-flash-lite"
GEMINI_EMBEDDING_MODEL = "models/gemini-embedding-001"


def configure_llama_index_settings() -> None:
    """Configure Google Gemini LLM and Embedding models in LlamaIndex."""
    gemini_key = os.getenv("GEMINI_API_KEY", "").strip()
    if not gemini_key:
        raise ValueError("GEMINI_API_KEY is not configured in .env file.")

    Settings.llm = Gemini(
        model_name=GEMINI_MODEL,
        api_key=gemini_key,
        temperature=0.2,
        max_tokens=4096,
    )
    Settings.embed_model = GeminiEmbedding(
        model_name=GEMINI_EMBEDDING_MODEL,
        api_key=gemini_key,
    )


def extract_text_from_pdf(pdf_path: str) -> str:
    """Extract clean text from all pages of a PDF file."""
    reader = PdfReader(pdf_path)
    pages = [page.extract_text() or "" for page in reader.pages]
    return "\n\n".join(pages).strip()


def load_web_visa_rules(visa_url: str) -> List[Document]:
    """Fetch and parse live visa rules from a web URL into a LlamaIndex Document."""
    try:
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko)"
        }
        response = requests.get(visa_url, headers=headers, timeout=15)
        response.raise_for_status()

        converter = html2text.HTML2Text()
        converter.ignore_links = False
        converter.ignore_images = True
        cleaned_text = converter.handle(response.text)

        max_characters = 25000
        if len(cleaned_text) > max_characters:
            cleaned_text = cleaned_text[:max_characters]

        return [Document(text=cleaned_text, metadata={"source": visa_url})]
    except Exception as error:
        fallback_text = f"Notice: Could not fetch live URL ({visa_url}): {error}."
        return [Document(text=fallback_text, metadata={"source": "visa_url_fallback"})]


def analyze_opportunity_and_visa(
    cv_file_path: str,
    opportunity_file_path: str,
    visa_url: Optional[str] = None,
    language: str = "en",
) -> str:
    """
    Main analysis pipeline:
    1. Loads CV and Opportunity PDFs.
    2. Fetches live Visa policy from the target URL.
    3. Builds an in-memory VectorStoreIndex combining all sources.
    4. Retrieves context and queries the LLM for evaluation.
    """
    configure_llama_index_settings()

    target_visa_url = visa_url or os.getenv(
        "VISA_RULES_URL",
        "https://en.wikipedia.org/wiki/Visa_policy_of_the_Schengen_Area",
    )

    cv_text = extract_text_from_pdf(cv_file_path)
    opportunity_text = extract_text_from_pdf(opportunity_file_path)

    pdf_docs = [
        Document(text=cv_text, metadata={"source": "candidate_cv", "file_name": os.path.basename(cv_file_path)}),
        Document(text=opportunity_text, metadata={"source": "opportunity_details", "file_name": os.path.basename(opportunity_file_path)}),
    ]
    web_docs = load_web_visa_rules(target_visa_url)
    all_documents = pdf_docs + web_docs

    # Build vector index and retrieve relevant visa regulations
    index = VectorStoreIndex.from_documents(all_documents)
    retriever = index.as_retriever(similarity_top_k=8)
    retrieved_nodes = retriever.retrieve("visa requirements immigration permits legal entry rules host country residency")
    visa_context = "\n\n".join([node.get_text() for node in retrieved_nodes])

    # Build evaluation prompt with extracted documents and retrieved context
    is_arabic = language.lower().startswith("ar")
    if is_arabic:
        prompt = f"""
أنت مستشار دولي خبير في تحليل الفرص الوظيفية وشؤون الهجرة وقوانين العمل الدولية.
قم بإجراء تحليل شامل، دقيق وموثق بنسبة 100% للمستندات التالية:

=== وثيقة السيرة الذاتية للمرشح (كاملة) ===
{cv_text}

=== وثيقة تفاصيل ومتطلبات الفرصة المستهدفة (كاملة) ===
{opportunity_text}

=== لوائح وسياسات التأشيرات المستخرجة من الويب ===
{visa_context}

⚠️ تعليمات حاسمة وإلزامية:
1. دقة البيانات الأساسية: استخرج الراتب والدرجة الوظيفية والموقع الدقيق للوظيفة (المدينة والدولة المستضيفة) وطبيعة العقد بدقة.
2. قيود التوظيف المحلي والإقامة: دقق في شرط التوظيف المحلي (Local recruitment) واشتراط الإقامة المسبقة ومسافة السفر اليومية (Commuting distance).
3. مطابقة كل متطلب على حدة: قارن كل متطلب ذُكر في الوظيفة مع سيرة المرشح وضع علامة [✅ متطابق] أو [🚩 غير متوفر / FLAGGED].
4. إبراز المزايا والعيوب: وضّح مزايا الوظيفة ولماذا تناسب المرشح، والعيوب والموانع ولماذا لا تناسب المرشح.

يرجى تقديم التقرير بدقة باللغة العربية الفصحى مع الأقسام الستة التالية:

### 1. 📋 نظرة عامة على الوظيفة والبيانات الأساسية:
- **المسمى الوظيفي والجهة المشغلة**: اسم الوظيفة والمنظمة والقسم.
- **مقر العمل الفعلي والدولة المستضيفة**: المدينة والدولة المحددة نصاً في الوثيقة.
- **الراتب والمزايا المالية والدرجة الوظيفية**: جدول الرواتب المذكور، الدرجة (مثال: G-3)، والعملة المحلية أو المزايا.
- **نوع العقد ومدته**: مدة العقد وإمكانية التمديد.
- **بيانات المرشح**: الاسم، الجنسية، ومحل الإقامة الحالي.
- **طبيعة الوظيفة والمهام الرئيسية**: ملخص شامل لما تدور حوله الوظيفة وأهم المهام اليومية المطلوبة.

### 2. 📊 جدول مطابقة المتطلبات والإشارات التحذيرية (FLAGS 🚩):
(نظّم جميع متطلبات الوظيفة ومقارنتها مع سيرة المرشح في جدول Markdown دقيق من 4 أعمدة):
⚠️ تنبيه تقني صارم: يجب أن يبدأ كل صف في الجدول بسطر جديد مستقل (Newline)، ولا تدمج الصفوف أبداً في سطر واحد:
| المتطلب الأساسي | المطلوب في الوظيفة | المتوفر في سيرة المرشح | نتيجة المطابقة |
| :--- | :--- | :--- | :--- |
| **المؤهل العلمي** | [المطلوب نصاً] | [المتوفر في السيرة] | [✅ متطابق / 🚩 غير متطابق] |
| **سنوات ونوع الخبرة** | [المطلوب نصاً] | [المتوفر في السيرة] | [✅ متطابق / 🚩 غير متطابق] |
| **اللغات المطلوبة** | [المطلوب نصاً] | [المتوفر في السيرة] | [✅ متطابق / 🚩 غير متطابق] |
| **المهارات التقنية والمكتبية** | [المطلوب نصاً] | [المتوفر في السيرة] | [✅ متطابق / 🚩 غير متطابق] |
| **شرط الإقامة القانونية وتصريح العمل ومسافة الانتقال** | [المطلوب نصاً] | [المتوفر في السيرة] | [✅ متطابق / 🚩 مانع حاسم] |

- **نسبة التوافق التقديرية الإجمالية**: (مثال: 45%).

### 3. 🌟 لماذا تناسب المرشح ومزايا الوظيفة (PROS):
- **أبرز مزايا الوظيفة**: السمعة المؤسسية، حزمة التعويضات، الاستقرار، وفرص التطوير.
- **نقاط القوة التوافقية**: المهارات والسمات المشتركة التي يمتلكها المرشح وتخدم دور العمل.

### 4. ⚠️ لماذا لا تناسب المرشح والعيوب والموانع الحاسمة (CONS):
- **الموانع القانونية الحاسمة**: مثل حصر التوظيف على السكان المحليين، اشتراط الإقامة المسبقة، أو عدم تقديم كفالة فيزا.
- **الفجوات المهارية أو عدم ملاءمة المسار المهني**: اختلاف التخصص أو نقص سنوات الخبرة المكتبية المحددة.
- **القيود المالية والجغرافية**: الدفع بالعملة المحلية دون بدلات اغتراب دولية أو اشتراط السكن ضمن مسافة الانتقال اليومي.

### 5. 🛂 التحليل القانوني للتأشيرة والإقامة:
- **التحقق من مقر العمل**: تأكيد الدولة المستضيفة.
- **لوائح التوظيف المحلي ورعاية التأشيرات**: هل تمنح المنظمة رعاية تأشيرة عمل أم تشترط إقامة سارية مسبقاً؟
- **المسار القانوني أو المانع النظامي**: توصيف وضع المرشح القانوني للدخول أو التوظيف.

### 6. 💡 القرار النهائي والتوصيات العملية:
- **التقييم والتوصية النهائية الحاسمة**: (غير مؤهل / موصى به بشروط / موصى به) مع تعليل جامع للسبب.
- **أهم 3 خطوات عملية استراتيجية بديلة للمرشح**: نصائح واقعية قابلة للتنفيذ الفوري.
"""
    else:
        prompt = f"""
You are an expert International Opportunity, Immigration & Employment Law Advisor.
Conduct an exhaustive, high-precision, and fact-based evaluation of the following documents:

=== CANDIDATE CV DOCUMENT (FULL TEXT) ===
{cv_text}

=== TARGET OPPORTUNITY SPECIFICATION (FULL TEXT) ===
{opportunity_text}

=== LIVE VISA POLICY & IMMIGRATION RULES ===
{visa_context}

⚠️ MANDATORY EVALUATION INSTRUCTIONS:
1. ACCURATE EXTRACTION: Accurately extract all concrete details stated in the Opportunity: salary scale, grade level (e.g. G-3), host country and city, contract duration, and candidate nationality/residence.
2. STRICT LOCAL RECRUITMENT & RESIDENCY AUDIT: Inspect for local recruitment constraints (e.g. General Service Staff recruited locally), requirements for pre-existing legal residency, valid work permits, and commuting distance.
3. MATCH EVERY REQUIREMENT IN A TABLE & FLAG GAPS: Explicitly compare every single requirement stated in the Opportunity against the candidate's CV in a clear 4-column Markdown Table and flag any unmet criteria with [🚩 UNMET / FLAGGED].
4. BALANCED PROS & CONS: Provide distinct, clear sections on why the opportunity fits the user (pros/advantages) and why it does NOT fit the user (cons/red flags/critical barriers).

Please provide the evaluation report in English with the following exact six sections:

### 1. 📋 JOB OVERVIEW & KEY DETAILS:
- **Job Title & Organization**: Exact position title, organizational unit, and hiring agency.
- **Stated Host Country & City**: Exact physical job location and duty station stated in the document.
- **Salary, Compensation & Grade Level**: Grade level (e.g., G-3), UN salary scale details, remuneration currency, and benefits.
- **Contract Type & Duration**: Term length (e.g. 1 year fixed-term) and extension possibilities.
- **Candidate Profile**: Candidate Name, Nationality, and Current Location.
- **Job Summary & Core Functions**: What the job is about and primary day-to-day responsibilities.

### 2. 📊 REQUIREMENT MATCHING & CRITICAL FLAGS TABLE (🚩):
(Structure every stated minimum requirement from the job against the candidate's CV in a clean 4-column Markdown Table):
⚠️ STRICT FORMATTING RULE: Every row of the Markdown table must be on its own separate line preceded by a newline (\n). Never collapse rows into a single line.
| Core Requirement | Required by Opportunity | Candidate CV Profile | Match Status & Flags |
| :--- | :--- | :--- | :--- |
| **Education Requirement** | [Stated requirement] | [Candidate profile] | [✅ MET / 🚩 UNMET] |
| **Experience Requirement** | [Stated requirement] | [Candidate profile] | [✅ MET / 🚩 UNMET] |
| **Languages Requirement** | [Stated requirement] | [Candidate profile] | [✅ MET / 🚩 UNMET] |
| **IT & Technical Skills** | [Stated requirement] | [Candidate profile] | [✅ MET / 🚩 UNMET] |
| **Legal Residency & Commuting Distance** | [Stated requirement] | [Candidate profile] | [✅ MET / 🚩 CRITICAL UNMET - DISQUALIFIER] |

- **Overall Match Percentage**: (e.g., 45%).

### 3. 🌟 WHY IT FITS & JOB ADVANTAGES (PROS):
- **Key Job Advantages**: Organization prestige, salary/benefits package, workplace stability, and career growth.
- **Areas of Skill Synergy**: Specific candidate strengths, qualifications, and transferable competencies that align with the role.

### 4. ⚠️ WHY IT DOES NOT FIT & RED FLAGS (CONS):
- **Critical Barriers & Disqualifiers**: Mandatory local recruitment, lack of pre-existing residency, and absence of visa sponsorship.
- **Skills/Background Mismatches**: Divergence between candidate's core specialization and the day-to-day office/administrative support functions.
- **Geographic & Compensation Constraints**: Paid in local currency without international relocation allowances; daily commuting distance requirement.

### 5. 🛂 VISA & LEGAL IMMIGRATION ANALYSIS:
- **Duty Station Verification**: Confirmation of the host country and physical office location.
- **Local Recruitment & Visa Policy**: Whether the employer offers visa sponsorship or strictly requires pre-existing local work authorization.
- **Applicable Visa Pathway or Legal Barrier**: Immigration rules that apply and legal impediments to hiring.

### 6. 💡 FINAL VERDICT & ACTIONABLE RECOMMENDATIONS:
- **Overall Final Verdict**: (Not Eligible / Conditionally Recommended / Recommended) with a concise, decisive explanation.
- **Next 3 Immediate Strategic Steps**: 3 actionable, realistic next steps for the candidate.
"""

    response = Settings.llm.complete(prompt)
    return str(response)
