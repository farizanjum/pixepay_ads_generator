# PixePay Ads Generator

A powerful Facebook Ads Library scraper and AI-powered ad creative generator built with Streamlit, Apify, and Google Gemini.

## 🚀 Features

### Facebook Ads Library Integration
- **Advanced Search**: Search Facebook ads by keywords, countries, and date ranges
- **Real-time Scraping**: Uses Apify's Facebook Ads Library Scraper for comprehensive data collection
- **Creative Extraction**: Automatically extracts ad images, videos, and metadata
- **Batch Processing**: Handle large volumes of ads efficiently

### AI-Powered Ad Generation
- **VU Engine Prompts**: Generate professional ad copy using proven VU Engine methodology
- **Google Gemini Integration**: Create stunning visuals using cutting-edge AI image generation
- **Variant Generation**: Produce multiple ad variations for A/B testing
- **Progress Tracking**: Real-time progress bars for generation processes

### Collection Management
- **Organized Storage**: Save and organize ads into custom collections
- **Bulk Operations**: Select, delete, and download multiple ads at once
- **Local Image Storage**: Images saved locally for offline access and reliability
- **Session Management**: Track generation sessions with full metadata

### Advanced Features
- **Multi-step Progress**: Detailed progress tracking for all operations
- **ZIP Downloads**: Download entire collections or sessions as compressed files
- **Responsive UI**: Modern, intuitive interface built with Streamlit
- **Error Handling**: Robust error handling with user-friendly messages

## 🛠️ Installation

### Prerequisites
- Python 3.8+
- Git
- Apify account (for Facebook Ads scraping)
- Google Gemini API key (for image generation)

### Setup

1. **Clone the repository:**
   ```bash
   git clone https://github.com/farizanjum/pixepay_ads_generator.git
   cd pixepay_ads_generator
   ```

2. **Create virtual environment:**
   ```bash
   python -m venv venv
   source venv/bin/activate  # On Windows: venv\Scripts\activate
   ```

3. **Install dependencies:**
   ```bash
   pip install -r requirements.txt
   ```

4. **Configure environment variables:**

   Copy `.env.example` to `.env` and fill in your API keys:
   ```bash
   cp .env.example .env
   ```

   Required environment variables:
   ```env
   # Apify API token for Facebook Ads scraping
   APIFY_API_TOKEN=your_apify_token_here

   # OpenAI API key (optional, for analysis)
   OPENAI_API_KEY=your_openai_key_here

   # Google Gemini API key (required for image generation)
   GOOGLE_API_KEY=your_gemini_key_here

   # OpenAI Assistant ID (optional)
   ANALYSIS_ASSISTANT_ID=your_assistant_id_here
   ```

## 🚀 Usage

### Running the Application

```bash
streamlit run app.py
```

The application will be available at `http://localhost:8501`

### Navigation

The app has 4 main tabs:

1. **Search**: Search and scrape Facebook ads
2. **External Ads Generator**: Upload images and generate ad variants
3. **Saved Collections**: View and manage saved ad collections
4. **Generated Ads**: View generated ad sessions

### Basic Workflow

1. **Search for Ads**: Use the Search tab to find relevant Facebook ads
2. **Save to Collections**: Save interesting ads to organized collections
3. **Generate Variants**: Use collections to generate AI-powered ad variants
4. **Download Results**: Export generated ads as ZIP files

## 📋 API Keys Setup

### Apify Setup
1. Sign up at [Apify](https://apify.com)
2. Get your API token from the dashboard
3. Use the Facebook Ads Library Scraper

### Google Gemini Setup
1. Visit [Google AI Studio](https://makersuite.google.com/app/apikey)
2. Create a new API key
3. Enable image generation permissions

## 🏗️ Architecture

### Core Components

- **app.py**: Main Streamlit application with UI and business logic
- **assistant_engine.py**: AI integration for prompt generation and image creation
- **Database**: SQLite-based storage for ads, collections, and sessions

### Key Technologies

- **Streamlit**: Web UI framework
- **Apify Client**: Facebook Ads scraping
- **Google Generative AI**: Image and text generation
- **SQLite**: Local database storage
- **Pandas**: Data manipulation

## 🔧 Development

### Code Structure

```
pixepay_ads_generator/
├── app.py                 # Main application
├── assistant_engine.py    # AI integration
├── requirements.txt       # Python dependencies
├── .env.example          # Environment template
├── .gitignore            # Git ignore rules
└── README.md             # This file
```

### Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes
4. Submit a pull request

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

## 🤝 Support

For support and questions:
- Open an issue on GitHub
- Check the documentation
- Review the code comments

## 🔄 Updates

Stay tuned for updates and new features! This project is actively maintained and improved.

---

**Built with ❤️ using Streamlit, Apify, and Google Gemini**
