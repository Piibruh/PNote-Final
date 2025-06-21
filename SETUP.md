# PNote Setup Guide

## Quick Setup

### 1. Environment Configuration

Create a `.env` file in the root directory with your Google Gemini API key:

```bash
# .env
GEMINI_API_KEY=your_actual_api_key_here
```

**Get your API key from:** https://makersuite.google.com/app/apikey

### 2. Install Dependencies

```bash
pip install -r requirements.txt
```

### 3. Run the Application

```bash
streamlit run app.py
```

## Environment Variables

| Variable | Description | Default |
|----------|-------------|---------|
| `GEMINI_API_KEY` | Google Gemini API key (required) | None |
| `TEXT_CHUNK_SIZE` | Size of text chunks for processing | 1000 |
| `TEXT_CHUNK_OVERLAP` | Overlap between text chunks | 150 |
| `VECTOR_DB_SEARCH_RESULTS` | Number of search results | 7 |

## Troubleshooting

### Common Issues

1. **"GEMINI_API_KEY not found"**
   - Make sure you have created the `.env` file
   - Verify your API key is correct
   - Check that the key is active in Google AI Studio

2. **Import errors**
   - Run `pip install -r requirements.txt` again
   - Make sure you're using Python 3.8+

3. **Database errors**
   - The app will automatically create necessary directories
   - Make sure you have write permissions in the project folder

### Getting Help

- Check the main README.md for detailed documentation
- Ensure all dependencies are properly installed
- Verify your API key is working with a simple test 