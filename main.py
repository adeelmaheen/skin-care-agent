import streamlit as st
from openai import OpenAI
import os
import base64
import requests
import json
from fpdf import FPDF
from fpdf.enums import XPos, YPos  # Add this import for new_x/new_y
from PIL import Image
import io
from dotenv import load_dotenv
import time

# Load environment variables
load_dotenv()

# Verify API key
if not os.getenv("OPENAI_API_KEY"):
    st.error("❌ OPENAI_API_KEY not found in .env file.")
    st.stop()

# Initialize OpenAI client
client = OpenAI(api_key=os.getenv("OPENAI_API_KEY"))

# Page configuration
st.set_page_config(
    page_title="🌿 SkinCare AI Assistant",
    page_icon="🌿",
    layout="wide"
)

# Multi-language support
LANGUAGES = {
    "en": "English",
    "es": "Español", 
    "fr": "Français",
    "de": "Deutsch",
    "hi": "हिन्दी",
    "ar": "العربية",
    "ja": "日本語"
}

translations = {
    "title": {
        "en": "🌿 Advanced Skin Care AI Assistant",
        "es": "🌿 Asistente IA Avanzado para el Cuidado de la Piel",
        "fr": "🌿 Assistant IA Avancé pour les Soins de la Peau",
        "de": "🌿 Erweiterte Hautpflege-KI-Assistent",
        "hi": "🌿 उन्नत त्वचा देखभाल AI सहायक",
        "ar": "🌿 مساعد الذكاء الاصطناعي المتقدم للعناية بالبشرة",
        "ja": "🌿 高度なスキンケアAIアシスタント"
    },
    "intro": {
        "en": "Get personalized skincare advice with AI-powered analysis using multiple specialized agents.",
        "es": "Obtén consejos personalizados con análisis de IA usando múltiples agentes especializados.",
        "fr": "Obtenez des conseils personnalisés avec une analyse IA utilisant plusieurs agents spécialisés.",
        "de": "Erhalten Sie personalisierte Hautpflegeberatung mit KI-Analyse durch mehrere spezialisierte Agenten.",
        "hi": "कई विशेषज्ञ एजेंटों का उपयोग करके AI-संचालित विश्लेषण के साथ व्यक्तिगत त्वचा देखभाल सलाह प्राप्त करें।",
        "ar": "احصل على نصائح مخصصة للعناية بالبشرة مع التحليل المدعوم بالذكاء الاصطناعي باستخدام وكلاء متخصصين متعددين۔",
        "ja": "複数の専門エージェントを使用したAI分析で、パーソナライズされたスキンケアアドバイスを取得します。"
    }
}

def t(key, lang="en"):
    return translations.get(key, {}).get(lang, key)

# Language selector
if "lang" not in st.session_state:
    st.session_state.lang = "en"

col1, col2 = st.columns([3, 1])
with col2:
    language = st.selectbox(
        "🌐 Language",
        options=list(LANGUAGES.keys()),
        format_func=lambda x: LANGUAGES[x],
        index=list(LANGUAGES.keys()).index(st.session_state.lang)
    )
    st.session_state.lang = language

# Inject custom CSS for beautiful UI
st.markdown("""
    <style>
    .main {
        background: linear-gradient(135deg, #e0f7fa 0%, #fce4ec 100%);
    }
    .stApp {
        font-family: 'Segoe UI', 'Arial', sans-serif;
        background: linear-gradient(135deg, #e0f7fa 0%, #fce4ec 100%);
    }
    .stTitle, .stMarkdown h1, .stMarkdown h2, .stMarkdown h3 {
        color: #00695c;
        font-weight: 700;
    }
    .stButton>button {
        background: linear-gradient(90deg,#43cea2,#185a9d);
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5em 1.5em;
        box-shadow: 0 2px 8px #b2dfdb;
    }
    .stDownloadButton>button {
        background: linear-gradient(90deg,#ffaf7b,#d76d77);
        color: white;
        border-radius: 8px;
        font-weight: bold;
        border: none;
        padding: 0.5em 1.5em;
        box-shadow: 0 2px 8px #f8bbd0;
    }
    .stTextArea textarea {
        background: #f1f8e9;
        border-radius: 8px;
        border: 1px solid #aed581;
        font-size: 1.1em;
    }
    .stSelectbox, .stSlider {
        background: #fffde7;
        border-radius: 8px;
        border: 1px solid #ffd54f;
    }
    .stFileUploader {
        background: #e3f2fd;
        border-radius: 8px;
        border: 1px solid #90caf9;
    }
    .stSuccess {
        background: #e0f2f1;
        color: #004d40;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5em;
    }
    .stWarning {
        background: #fff3e0;
        color: #e65100;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5em;
    }
    .stInfo {
        background: #e3f2fd;
        color: #01579b;
        border-radius: 8px;
        font-weight: bold;
        padding: 0.5em;
    }
    .stMarkdown {
        font-size: 1.1em;
    }
    </style>
""", unsafe_allow_html=True)

# Title and intro with emoji and colored box
st.markdown(
    f"""
    <div style='background:linear-gradient(90deg,#43cea2,#185a9d);padding:1.5em 1em;border-radius:16px;margin-bottom:1em;'>
        <h1 style='color:white;margin-bottom:0.2em;'>{t("title", language)}</h1>
        <p style='color:#e0f7fa;font-size:1.2em;'>{t("intro", language)}</p>
    </div>
    """, unsafe_allow_html=True
)

# Tool Functions
def search_pubmed_research(topic: str) -> str:
    """Search PubMed for dermatology research papers."""
    try:
        # Clean the topic for URL encoding
        clean_topic = topic.strip().replace(' ', '+')
        base_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esearch.fcgi"
        params = {
            "db": "pubmed",
            "term": f"{clean_topic}+AND+(dermatology+OR+skin+OR+skincare)",
            "retmode": "json",
            "retmax": "5",
            "sort": "relevance"
        }
        
        response = requests.get(base_url, params=params, timeout=15)
        response.raise_for_status()  # Raise an exception for bad status codes
        
        data = response.json()
        id_list = data.get("esearchresult", {}).get("idlist", [])
        count = data.get("esearchresult", {}).get("count", "0")
        
        if id_list:
            # Get additional details for first few papers
            details_url = "https://eutils.ncbi.nlm.nih.gov/entrez/eutils/esummary.fcgi"
            details_params = {
                "db": "pubmed",
                "id": ",".join(id_list[:3]),
                "retmode": "json"
            }
            
            try:
                details_response = requests.get(details_url, params=details_params, timeout=10)
                if details_response.status_code == 200:
                    details_data = details_response.json()
                    papers = []
                    for paper_id in id_list[:3]:
                        if paper_id in details_data.get("result", {}):
                            title = details_data["result"][paper_id].get("title", "No title available")
                            papers.append(f"• {title[:100]}..." if len(title) > 100 else f"• {title}")
                    
                    result = f"✅ **Found {count} research papers** on '{topic}' related to dermatology:\n\n"
                    result += "\n".join(papers)
                    result += f"\n\n🔗 [View all results on PubMed](https://pubmed.ncbi.nlm.nih.gov/?term={clean_topic}+AND+(dermatology+OR+skin+OR+skincare))"
                    return result
                else:
                    return f"✅ Found {count} research papers on '{topic}' in dermatology. PubMed IDs: {', '.join(id_list[:5])}"
            except:
                return f"✅ Found {count} research papers on '{topic}' in dermatology. PubMed IDs: {', '.join(id_list[:5])}"
        else:
            return f"🔍 No specific research papers found for '{topic}' in dermatology databases. Try more general terms like 'acne treatment' or 'skin aging'."
            
    except requests.RequestException as e:
        return f"🌐 Unable to connect to PubMed research database. Please check your internet connection."
    except Exception as e:
        return f"⚠️ Research search temporarily unavailable. Error: {str(e)[:100]}"

def get_herbal_remedies(skin_condition: str, skin_type: str) -> str:
    """Get herbal and natural remedies for specific skin conditions."""
    herbal_db = {
        "acne": {
            "oily": "🌿 Tea tree oil (diluted), neem paste, turmeric mask, green tea toner",
            "dry": "🌿 Honey mask, aloe vera gel, chamomile tea compress, rose water",
            "sensitive": "🌿 Calendula cream, oatmeal mask, cucumber slices, mild aloe vera",
            "combination": "🌿 Clay mask on T-zone, honey on dry areas, witch hazel toner",
            "normal": "🌿 Tea tree oil (diluted), honey mask, green tea toner"
        },
        "dryness": {
            "all": "🌿 Coconut oil, shea butter, avocado mask, hyaluronic acid serum, ceramide cream"
        },
        "redness": {
            "all": "🌿 Aloe vera gel, chamomile compress, green tea ice cubes, licorice root extract"
        },
        "aging": {
            "all": "🌿 Rosehip oil, vitamin C serum, retinol alternatives (bakuchiol), peptide creams"
        },
        "dark_spots": {
            "all": "🌿 Vitamin C, kojic acid, arbutin, licorice extract, lemon juice (diluted)"
        }
    }
    
    condition_key = skin_condition.lower()
    for key in herbal_db.keys():
        if key in condition_key:
            remedies = herbal_db[key]
            if skin_type in remedies:
                return f"🌿 **Herbal Remedies for {skin_condition}:**\n{remedies[skin_type]}"
            elif "all" in remedies:
                return f"🌿 **Herbal Remedies for {skin_condition}:**\n{remedies['all']}"
    
    return "🌿 **General Herbal Care:** Aloe vera, honey masks, green tea, and gentle plant-based cleansers are universally beneficial."

def get_home_remedies(issue: str) -> str:
    """Get home remedies using common household items."""
    home_remedies = {
        "acne": "🏠 **Home Remedies:** Ice cubes for inflammation, honey mask (20min), oatmeal scrub, steam facial with hot water",
        "dryness": "🏠 **Home Remedies:** Milk compress, honey-yogurt mask, olive oil massage, cucumber slices",
        "oily_skin": "🏠 **Home Remedies:** Clay mask, egg white mask, tomato slices, lemon-honey toner (diluted)",
        "dark_circles": "🏠 **Home Remedies:** Cold tea bags, cucumber slices, cold spoon compress, potato slices",
        "sunburn": "🏠 **Home Remedies:** Cool milk compress, aloe vera, cold shower, avoid further sun exposure"
    }
    
    for key, remedy in home_remedies.items():
        if key in issue.lower():
            return remedy
    
    return "🏠 **General Home Care:** Keep skin clean, use lukewarm water, moisturize regularly, and protect from sun."

def get_exercise_recommendations(skin_concern: str) -> str:
    """Get exercise recommendations for better skin health."""
    exercises = {
        "acne": "💪 **Exercises for Acne:** Face yoga, lymphatic drainage massage, cardiovascular exercises (shower immediately after), avoid touching face during workouts",
        "aging": "💪 **Anti-Aging Exercises:** Facial yoga, neck stretches, scalp massage, resistance training to boost collagen",
        "circulation": "💪 **For Better Circulation:** Cardio exercises, inverted poses (legs up wall), face massage, deep breathing exercises",
        "stress": "💪 **Stress-Relief for Skin:** Yoga, meditation, walking in nature, progressive muscle relaxation"
    }
    
    for key, exercise in exercises.items():
        if key in skin_concern.lower():
            return exercise
    
    return "💪 **General Skin Exercises:** Regular cardio improves circulation, facial massage boosts lymphatic drainage, and stress-reduction activities help overall skin health."

def get_dermatologist_advice(condition: str) -> str:
    """Provide general dermatologist-level advice (not medical diagnosis)."""
    advice = {
        "acne": "👨‍⚕️ **Professional Insight:** Consider salicylic acid or benzoyl peroxide products. Avoid over-washing. If severe, consult dermatologist for prescription options.",
        "eczema": "👨‍⚕️ **Professional Insight:** Maintain skin barrier with ceramide-based moisturizers. Identify and avoid triggers. Consider seeing dermatologist for severe cases.",
        "psoriasis": "👨‍⚕️ **Professional Insight:** This appears to be a chronic condition requiring professional treatment. Please consult a dermatologist for proper diagnosis and treatment plan.",
        "rosacea": "👨‍⚕️ **Professional Insight:** Avoid known triggers (spicy food, alcohol, extreme temperatures). Use gentle, fragrance-free products. Dermatologist consultation recommended.",
        "melanoma": "👨‍⚕️ **URGENT:** Any suspicious moles or changing spots should be examined by a dermatologist immediately. Use ABCDE rule: Asymmetry, Border, Color, Diameter, Evolution."
    }
    
    condition_lower = condition.lower()
    for key, recommendation in advice.items():
        if key in condition_lower:
            return recommendation
    
    return "👨‍⚕️ **General Professional Advice:** Maintain consistent skincare routine, use sunscreen daily, and consult dermatologist for persistent or concerning skin issues."

def sanitize_text_for_pdf(text):
    """Sanitize text to remove or replace characters not supported by the helvetica font."""
    if not text:
        return text
    
    # Replace common Unicode characters with ASCII equivalents
    replacements = {
        '"': '"',  # Left double quotation mark
        '"': '"',  # Right double quotation mark
        ''': "'",  # Left single quotation mark
        ''': "'",  # Right single quotation mark
        '–': '-',   # En dash
        '—': '-',   # Em dash
        '…': '...', # Horizontal ellipsis
        '€': 'EUR', # Euro sign
        '£': 'GBP', # Pound sign
        '¥': 'JPY', # Yen sign
        '©': '(c)', # Copyright sign
        '®': '(R)', # Registered trademark sign
        '™': '(TM)', # Trademark sign
    }
    
    # Apply replacements
    for unicode_char, replacement in replacements.items():
        text = text.replace(unicode_char, replacement)
    
    # Remove any remaining non-ASCII characters that aren't supported
    # This preserves basic ASCII characters (0-127) which are safe for helvetica font
    sanitized = ''.join(char if ord(char) < 128 else '?' for char in text)
    
    return sanitized

# Agent class to simulate OpenAI Agents SDK functionality
class SkinCareAgent:
    def __init__(self, name: str, instructions: str, tools: list):
        self.name = name
        self.instructions = instructions
        self.tools = tools
    
    def analyze(self, user_input: str, image_data: str = None, skin_type: str = "normal"):
        """Analyze user input and provide specialized advice."""
        # Prepare messages for OpenAI API
        messages = [
            {"role": "system", "content": f"{self.instructions} User has {skin_type} skin type."},
        ]
        
        # Add user message with text and optionally image
        user_message = {"role": "user", "content": []}
        
        if user_input:
            user_message["content"].append({"type": "text", "text": user_input})
        
        if image_data:
            user_message["content"].append({
                "type": "image_url",
                "image_url": {
                    "url": f"data:image/jpeg;base64,{image_data}",
                    "detail": "high"
                }
            })
        
        # If no content parts, add default text
        if not user_message["content"]:
            user_message["content"] = [{"type": "text", "text": "Please provide general skincare advice."}]
        
        messages.append(user_message)
        
        try:
            # Use current OpenAI models - gpt-4o for vision capabilities
            model = "gpt-4o" if image_data else "gpt-4o-mini"
            response = client.chat.completions.create(
                model=model,
                messages=messages,
                max_tokens=1500,
                temperature=0.7
            )
            
            base_response = response.choices[0].message.content
            
            # Apply tools based on agent type
            tool_results = []
            if "herbal" in self.name.lower() and user_input:
                tool_results.append(get_herbal_remedies(user_input, skin_type))
            
            if "home" in self.name.lower() and user_input:
                tool_results.append(get_home_remedies(user_input))
            
            if "exercise" in self.name.lower() and user_input:
                tool_results.append(get_exercise_recommendations(user_input))
            
            if "dermatologist" in self.name.lower() and user_input:
                tool_results.append(get_dermatologist_advice(user_input))
            
            if "research" in self.name.lower() and user_input:
                tool_results.append(search_pubmed_research(user_input))
            
            # Combine base response with tool results
            if tool_results:
                combined_response = f"{base_response}\n\n" + "\n\n".join(tool_results)
            else:
                combined_response = base_response
            
            return combined_response
            
        except Exception as e:
            error_msg = str(e)
            if "model" in error_msg.lower() and "not found" in error_msg.lower():
                return f"❌ Model error with {self.name}. Please check your OpenAI API access and model availability."
            elif "quota" in error_msg.lower() or "rate" in error_msg.lower():
                return f"❌ API quota exceeded. Please try again later or check your OpenAI billing."
            elif "invalid" in error_msg.lower() and "key" in error_msg.lower():
                return f"❌ Invalid API key. Please check your OPENAI_API_KEY in the .env file."
            else:
                return f"❌ Error analyzing with {self.name}: {error_msg}"

# Define specialized agents
agents = {
    "Vision Expert": SkinCareAgent(
        name="Vision Skincare Expert", 
        instructions="You are a professional skincare consultant. Analyze the uploaded image and provide detailed, safe skincare advice. Focus on identifying visible skin conditions and recommend appropriate treatments. Always advise consulting a dermatologist for serious conditions.",
        tools=["image_analysis"]
    ),
    "Herbal Specialist": SkinCareAgent(
        name="Herbal Skincare Specialist",
        instructions="You are an expert in natural and herbal skincare remedies. Provide safe, natural, plant-based solutions for skin concerns. Focus on herbs, essential oils, and natural ingredients. Always mention patch testing for new ingredients.",
        tools=["herbal_remedies"]
    ),
    "Home Remedy Expert": SkinCareAgent(
        name="Home Remedy Expert",
        instructions="You specialize in home-based skincare solutions using common household items. Provide practical, accessible remedies that people can easily make at home. Focus on kitchen ingredients and DIY treatments.",
        tools=["home_remedies"]
    ),
    "Exercise & Wellness": SkinCareAgent(
        name="Exercise & Wellness Coach",
        instructions="You focus on how physical activity, stress management, and lifestyle factors affect skin health. Provide exercise recommendations and wellness tips that improve skin from the inside out.",
        tools=["exercise_recommendations"]
    ),
    "Dermatologist AI": SkinCareAgent(
        name="Dermatologist AI Advisor",
        instructions="You provide professional dermatological insights and advice. Focus on evidence-based recommendations, product suggestions, and when to seek professional medical help. Never provide medical diagnoses.",
        tools=["dermatologist_advice"]
    ),
    "Research Assistant": SkinCareAgent(
        name="Research Assistant",
        instructions="You help find and summarize relevant dermatological research and scientific studies. Provide evidence-based information and cite scientific findings when possible.",
        tools=["research"]
    )
}

# Main interface
with st.container():
    col1, col2 = st.columns([2, 1])
    with col1:
        st.markdown("#### 🤖 Choose Your AI Specialist")
        selected_agent = st.selectbox(
            "Choose Your AI Specialist",  # <-- non-empty label
            options=list(agents.keys()),
            help="Each agent specializes in different aspects of skincare",
            label_visibility="collapsed"  # <-- hides label visually, keeps accessibility
        )
        st.markdown("#### 🧴 Select Your Skin Type")
        skin_type = st.select_slider(
            "Select Your Skin Type",  # <-- non-empty label
            options=["oily", "combination", "normal", "dry", "sensitive"],
            value="normal",
            label_visibility="collapsed"
        )
        st.markdown("#### 📝 Input Your Question or Concern")
        user_input = st.text_area(
            "Describe your skin concern",  # <-- non-empty label
            placeholder="E.g., I have acne on my forehead, dark spots on cheeks, dry patches around eyes...",
            height=100,
            label_visibility="collapsed"
        )
        if st.button("🎤 Voice Input (Coming Soon)"):
            st.info("Voice input feature will be available in future updates. For now, please use text input.")

    with col2:
        st.markdown("#### 📸 Upload Skin Image")
        uploaded_file = st.file_uploader(
            "Upload a clear photo of your skin",  # <-- non-empty label
            type=["png", "jpg", "jpeg"],
            help="For best results, use good lighting and focus on the area of concern",
            label_visibility="collapsed"
        )
        if uploaded_file is not None:
            image = Image.open(uploaded_file)
            st.image(image, caption="Uploaded Image", use_container_width=True)

# Analysis section with spinner and colored box
if st.button("🔬 Get AI Analysis & Recommendations", type="primary"):
    if not user_input.strip() and uploaded_file is None:
        st.warning("⚠️ Please either upload an image or enter a question/concern.")
    else:
        with st.spinner(f"🤖 {selected_agent} is analyzing..."):
            image_data = None
            if uploaded_file is not None:
                image_bytes = uploaded_file.getvalue()
                image_data = base64.b64encode(image_bytes).decode()
            agent = agents[selected_agent]
            response = agent.analyze(user_input, image_data, skin_type)
            st.session_state.last_analysis = response
            st.session_state.last_agent = selected_agent
            st.session_state.user_input = user_input
            st.session_state.skin_type = skin_type
            st.success(f"✅ Analysis complete from {selected_agent}")
            st.markdown(
                f"""
                <div style='background:linear-gradient(90deg,#ffaf7b,#d76d77);padding:1em;border-radius:16px;margin-top:1em;'>
                    <h3 style='color:white;'>💡 AI Analysis & Recommendations</h3>
                    <div style='color:#fffde7;'>{response}</div>
                </div>
                """, unsafe_allow_html=True
            )

# PDF Download section with styled button
if hasattr(st.session_state, 'last_analysis'):
    st.markdown("---")
    if st.button("📥 Download Analysis as PDF"):
        pdf = FPDF()
        pdf.add_page()
        pdf.set_font("helvetica", size=12)  # Use helvetica instead of Arial
        pdf.set_font("helvetica", 'B', 16)
        pdf.cell(0, 10, "Skincare AI Analysis Report", new_x=XPos.LMARGIN, new_y=YPos.NEXT, align='C')
        pdf.ln(5)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, f"Analyzed by: {st.session_state.last_agent}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.cell(0, 10, f"Skin Type: {st.session_state.skin_type.title()}", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.ln(5)
        if hasattr(st.session_state, 'user_input') and st.session_state.user_input:
            pdf.set_font("helvetica", 'B', 12)
            pdf.cell(0, 10, "Your Question:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
            pdf.set_font("helvetica", size=10)
            sanitized_user_input = sanitize_text_for_pdf(st.session_state.user_input)
            pdf.multi_cell(0, 6, sanitized_user_input)
            pdf.ln(5)
        pdf.set_font("helvetica", 'B', 12)
        pdf.cell(0, 10, "AI Analysis & Recommendations:", new_x=XPos.LMARGIN, new_y=YPos.NEXT)
        pdf.set_font("helvetica", size=10)
        analysis_text = st.session_state.last_analysis
        # Sanitize text to remove unsupported Unicode characters
        sanitized_analysis_text = sanitize_text_for_pdf(analysis_text)
        pdf.multi_cell(0, 6, sanitized_analysis_text)
        # pdf.output(dest='S') returns bytearray, convert to bytes for Streamlit
        pdf_output = pdf.output(dest='S')
        pdf_bytes = bytes(pdf_output)  # Convert bytearray to bytes
        st.download_button(
            label="📥 Download PDF Report",
            data=pdf_bytes,
            file_name=f"skincare_analysis_{selected_agent.lower().replace(' ', '_')}.pdf",
            mime="application/pdf"
        )

# Footer with icons and styled box
st.markdown("---")
st.markdown(
    """
    <div style='text-align: center; color: #666; background: #f1f8e9; border-radius: 16px; padding: 1em; margin-top: 2em;'>
    💡 <b>Powered by OpenAI GPT-4o</b> | 
    🔬 <b>Multi-Agent AI System</b> | 
    ⚕️ <b>For Educational Use Only - Not Medical Advice</b><br>
    <span style='color:#00695c;'>Always consult qualified healthcare professionals for serious skin conditions</span>
    </div>
    """, 
    unsafe_allow_html=True
)

# Initialize session state
if 'messages' not in st.session_state:
    st.session_state.messages = []
