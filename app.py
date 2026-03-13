import streamlit as st
import ollama
from PIL import Image
import io

# --- UI Header ---
st.set_page_config(page_title="Foodiemeasure AI", page_icon="🥗")
st.title("🥗 Foodiemeasure AI")
st.subheader("Your AI Nutritionist for Gout Management")

# --- Step 1: Image Upload ---
uploaded_file = st.file_uploader("Take a photo of your meal...", type=['jpg', 'jpeg', 'png'])

if uploaded_file is not None:
    # Display the image
    image = Image.open(uploaded_file)
    st.image(image, caption='Your Meal', use_container_width=True)
    
    if st.button("Analyze My Meal"):
        with st.spinner('Calculating calories and purines...'):
            try:
                # Convert image to bytes for Ollama
                img_byte_arr = io.BytesIO()
                image.save(img_byte_arr, format='PNG')
                img_bytes = img_byte_arr.getvalue()

                # --- Step 2: Call Ollama ---
                response = ollama.chat(
                    model='moondream',
                    messages=[{
                        'role': 'user',
                        'content': '''Analyze the image and provide a nutritional report. 
Strictly follow this layout:

- Name: (Write the food name here)
- Calories: (Estimated total calories) kcal
- Purine Level: (Low, Medium, or High)

Do not use placeholders. Provide real estimates based on the image.''', 
                        'images': [img_bytes]
                    }]
                )

                # --- Step 3: Display Results ---
                st.success("Analysis Complete!")
                st.markdown(response['message']['content'])
                
            except Exception as e:
                st.error(f"Error: {e}")

# --- Sidebar info ---
st.sidebar.info("This app uses a local AI model (Llava via Ollama) to protect your privacy.")