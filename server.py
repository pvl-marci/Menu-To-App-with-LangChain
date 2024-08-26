from fastapi import FastAPI, File, UploadFile
from langchain.prompts import (
    HumanMessagePromptTemplate,
    ChatPromptTemplate,
)
from langchain_openai import ChatOpenAI
from langchain import globals
import base64
from mimetypes import guess_type
import pandas as pd
import psycopg2
import requests
import dotenv
import os
from io import StringIO
import csv

# Load environment variables from .env file
dotenv.load_dotenv()

# Load variables from environment
DB_HOST = os.getenv("DB_HOST")
DB_PORT = os.getenv("DB_PORT")
DB_NAME = os.getenv("DB_NAME")
DB_USER = os.getenv("DB_USER")
DB_PASS = os.getenv("DB_PASS")
OPENAI_API_KEY = os.getenv("OPENAI_API_KEY")
LANGSMITH_API_KEY = os.getenv("LANGSMITH_API_KEY")


# Define your database connection parameters
conn_params = {
    "host": DB_HOST,
    "port": DB_PORT,
    "database": DB_NAME,
    "user": DB_USER,
    "password": DB_PASS,
}


# Function to encode a local image into data URL
def image_to_data_url(image_bytes: bytes, mime_type: str) -> str:

    base64_encoded_data = base64.b64encode(image_bytes).decode("utf-8")
    return f"data:{mime_type};base64,{base64_encoded_data}"


def create_csv_from_image(image_path):

    prompt_template = HumanMessagePromptTemplate.from_template(
        template=[
            {
                "type": "text",
                "text": "only create a csv from this image with the columns: dish, description, price. The price is numeric without currency symbol. Just give the csv file as output. Your response should be a list of comma separated values, eg: `foo, bar, baz` or `foo,bar,baz`. Remove commas if they are part of the value.",
            },
            {
                "type": "image_url",
                "image_url": "{encoded_image_url}",
            },
        ],
    )

    summarize_image_prompt = ChatPromptTemplate.from_messages([prompt_template])

    gpt4o_llm = llm = ChatOpenAI(
        # hard coded cause of syntax error
        temperature=0,
        model_name="gpt-4o",
    )

    gpt4_image_chain = summarize_image_prompt | gpt4o_llm

    # page3_encoded = image_to_data_url(image_path)

    response = gpt4_image_chain.invoke(input={"encoded_image_url": image_path})
    print(response.content)

    df = pd.read_csv(StringIO(response.content))
    # Add column names
    column_names = ["dish", "description", "price"]
    df.columns = column_names
    # Save the DataFrame to a CSV file
    csv_path = "data.csv"
    df.to_csv(csv_path, index=False, header=True)
    return csv_path


# Function to update database with the LLM created CSV
def update_table(filepath):
    # Create a connection to the PostgreSQL database
    conn = psycopg2.connect(**conn_params)

    # Read the CSV file into a DataFrame
    df = pd.read_csv(filepath)

    # Iterate through the DataFrame and update the table
    for index, row in df.iterrows():
        dish = row["dish"]
        description = row["description"]
        price = row["price"]

        # Define the SQL query to insert or update the table
        query = """
        INSERT INTO Users (dish, description, price)
        VALUES (%s, %s, %s)
        ON CONFLICT (dish) DO UPDATE SET description = EXCLUDED.description, price = EXCLUDED.price;
        """

        # Query the database
        with conn.cursor() as cur:
            cur.execute(query, (dish, description, price))
            conn.commit()

    print("Table updated successfully!")

    # Close the database connection
    conn.close()
    # Delete the CSV file
    os.remove("data.csv")


# Create a FastAPI instance
app = FastAPI()


# Route that handles image uploads
@app.post("/upload")
async def upload_image(file: UploadFile = File(...)):
    # Read the file data as bytes
    image_bytes = await file.read()

    # Guess the MIME type based on the file name
    mime_type, _ = guess_type(file.filename)
    if mime_type is None:
        mime_type = "image/png"  # Default to PNG if MIME type is unknown

    # Convert the image to a Base64-encoded data URL
    create_csv_from_image(image_to_data_url(image_bytes, mime_type))
    update_table("data.csv")
