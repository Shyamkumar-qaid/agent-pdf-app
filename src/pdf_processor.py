import os
import fitz  # PyMuPDF
import pdfplumber
import openai
from dotenv import load_dotenv

class PDFIntelligentProcessor:
    def __init__(self):
        """
        Initialize the PDF processor with OpenAI configuration
        """
        # Load environment variables
        load_dotenv()
        
        # Get OpenAI API key
        self.api_key = os.getenv("OPENAI_API_KEY")
        if not self.api_key:
            raise ValueError("OpenAI API Key not found. Please set it in .env file.")
        
        # Initialize OpenAI client
        self.client = openai.OpenAI(api_key=self.api_key)
        
        # Set up input and output directories
        self.script_dir = os.path.dirname(os.path.abspath(__file__))
        self.input_dir = os.path.join(self.script_dir, "..", "input")
        self.output_dir = os.path.join(self.script_dir, "..", "output")
        
        # Create output directory if it doesn't exist
        os.makedirs(self.output_dir, exist_ok=True)

    def extract_text_from_pdf(self, pdf_path):
        """
        Extract text from PDF using PyMuPDF for better text extraction
        
        Args:
            pdf_path (str): Path to the input PDF
        
        Returns:
            list: List of text for each page
        """
        try:
            doc = fitz.open(pdf_path)
            page_texts = []
            
            for page in doc:
                # Extract text from the page
                page_text = page.get_text()
                page_texts.append(page_text)
            
            doc.close()
            return page_texts
        except Exception as e:
            print(f"Error extracting text: {e}")
            return []

    def process_command_with_gpt(self, text, command):
        """
        Use GPT to process text modification command
        
        Args:
            text (str): Original text
            command (str): Modification instruction
        
        Returns:
            str: Modified text
        """
        try:
            response = self.client.chat.completions.create(
                model="gpt-4-turbo-preview",
                messages=[
                    {"role": "system", "content": "You are an AI assistant that edits text precisely."},
                    {"role": "user", "content": f"Command: {command}\n\nOriginal Text:\n{text}"}
                ]
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            print(f"Error processing with GPT: {e}")
            return text

    def replace_text_in_pdf(self, input_filename, output_filename, command):
        """
        Replace text in PDF while preserving original formatting
        
        Args:
            input_filename (str): Input PDF filename
            output_filename (str): Output PDF filename
            command (str): Text modification instruction
        """
        # Construct full paths
        input_path = os.path.join(self.input_dir, input_filename)
        output_path = os.path.join(self.output_dir, output_filename)

        # Extract text from each page
        page_texts = self.extract_text_from_pdf(input_path)
        
        if not page_texts:
            print("❌ No text extracted from the PDF.")
            return

        # Process each page text using GPT
        modified_page_texts = []
        for text in page_texts:
            modified_text = self.process_command_with_gpt(text, command)
            modified_page_texts.append(modified_text)

        # Open original PDF
        try:
            doc = fitz.open(input_path)
            
            # Create a new PDF with modified text
            new_doc = fitz.open()
            
            for page, modified_text in zip(doc, modified_page_texts):
                # Create a new page with the same size and rotation as the original
                new_page = new_doc.new_page(width=page.rect.width, height=page.rect.height)
                
                # Insert modified text
                new_page.insert_text((50, 50), modified_text, fontsize=11)
                
                # Attempt to copy existing images or other elements (if possible)
                for img in page.get_images(full=True):
                    xref = img[0]
                    base_image = doc.extract_image(xref)
                    image_bytes = base_image["image"]
                    
                    # Insert image at its original location
                    new_page.insert_image(page.rect, stream=image_bytes)

            # Save modified PDF
            new_doc.save(output_path)
            
            # Close documents
            doc.close()
            new_doc.close()
            
            print(f"✅ PDF processed successfully: {output_path}")
        
        except Exception as e:
            print(f"❌ Error processing PDF: {e}")

def main():
    # Create processor instance
    processor = PDFIntelligentProcessor()
    
    # Example usage
    input_pdf = "sample.pdf"
    output_pdf = "modified_sample.pdf"
    modification_command = "Replace all mentions of 'Startup' with 'Enterprise'. Maintain the original context and tone."
    
    # Process PDF
    processor.replace_text_in_pdf(input_pdf, output_pdf, modification_command)

if __name__ == "__main__":
    main()