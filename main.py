import os
import time
from pathlib import Path
from io import BytesIO
import streamlit as st
from dotenv import load_dotenv
from google import genai
from PIL import Image
import tempfile
import mimetypes

# Loading API key
load_dotenv()

API_KEY = os.getenv("GOOGLE_API_KEY")

if not API_KEY:
    st.error("Please add GOOGLE_API_KEY to your .env file.")
    st.stop()

client = genai.Client(api_key=API_KEY)
MODEL = "gemini-3.6-flash"
st.set_page_config(page_title="StyleManaging AI",layout="centered")

st.title("StyleManage AI")
st.write("Your AI stylist ideas for better outfit ideas, clour combos and perfect accessories")

col1, col2 = st.columns(2)

with col1:
    occasion = st.selectbox(
        "Choose your occasion",
        [
            "College",
            "Office",
            "Party",
            "Wedding",
            "Casual Outing"
        ]
    )

with col2:
    style = st.selectbox(
        "Choose your preferred style",
        [
            "Casual",
            "Minimalist",
            "Trendy",
            "Elegant",
            "Traditional Fusion"
        ]
    )
option=st.radio(
    "choose the input data type",
    ["text","image","audio","video"],
    horizontal=True
)


text = st.text_area(
    "Your fashion question",
    placeholder= ("You can ask for your fashion advice over here")
)

file = None
if option=="image":
    #creating option to upload image
    file=st.file_uploader("Upload image",type=["jpg","jpeg","png"])

elif option=="audio":
    #creating option to upload audio
    file=st.file_uploader("Upload audio",type=["mp3","wav"])

elif option=="video":
    #creating option to upload video
    file=st.file_uploader("Upload video",type=["mp4","mov","avi"])

def create_prompt():

    return f"""
    You are StyleMate AI, a friendly personal fashion stylist.

    Occasion: {occasion}
    Preferred style: {style}

    User's text:
    {text.strip() or "Analyze my uploaded media and suggest an outfit."}

    Your task:
    1. Identify relevant visible clothing items when media is provided.
    2. Suggest suitable outfit combinations.
    3. Recommend matching colors.
    4. Suggest shoes, bags, and accessories.
    5. Give practical styling tips for the selected occasion.
    6. Offer alternative combinations when useful.

    For audio, understand the spoken request.
    For video, consider the clothing and relevant visual details.
    Do not invent details that are not visible or provided.
    Be friendly, respectful, and practical.
    """

def upload_media(file_path, wait_for_processing=False):
    mime_type = mimetypes.guess_type(file_path)[0]
    media_file = client.files.upload(file=file_path, config={"mime_type": mime_type})

    if wait_for_processing:
        while media_file.state.name != "ACTIVE":

            if media_file.state.name == "FAILED":
                st.error("Gemini could not process the video.")
                return None

            time.sleep(2)
            media_file = client.files.get(name=media_file.name)

    return media_file

if st.button("My Fashion Advice", type="primary"):

    if option != "text" and file is None:

        st.warning("Please upload a file first.")
    else:

        prompt = create_prompt()
        try:

            with st.spinner(
                "Your AI stylist is preparing recommendations..."
            ):
                if option == "text":

                    response = client.models.generate_content(
                        model=MODEL,
                        contents=prompt
                    )
                    st.subheader("Your Fashion Advice")
                    st.write(response.text)

                elif option == "image":

                    image = Image.open(
                        BytesIO(file.getvalue())
                    )

                    response = client.models.generate_content(
                        model=MODEL,
                        contents=[prompt, image]
                    )
                    st.subheader("Your Fashion Advice")
                    st.write(response.text)
                
                else:
                    suffix = Path(file.name).suffix
                    with tempfile.NamedTemporaryFile(delete=False,suffix=suffix) as temp_file:

                        temp_file.write(file.getvalue())
                        temp_path = temp_file.name

                    media_file = upload_media(
                        temp_path,
                        wait_for_processing=(option == "video")
                    )

                    response = client.models.generate_content(
                        model=MODEL,
                        contents=[prompt, media_file]
                    )
                    st.subheader("Your Fashion Advice")
                    st.write(response.text)
                    
        except Exception as error:

            st.error(
                f"Something went wrong: {error}"
            )
