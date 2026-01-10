#!/bin/bash

echo "🎓 Setting up PLI Weekly Digest..."
echo ""

# Create virtual environment
echo "📦 Creating virtual environment..."
python3 -m venv venv

# Activate virtual environment
echo "✅ Activating virtual environment..."
source venv/bin/activate

# Install dependencies
echo "📥 Installing dependencies..."
pip install --upgrade pip
pip install -r requirements.txt

# Create .env file if it doesn't exist
if [ ! -f .env ]; then
    echo "📝 Creating .env file..."
    cp .env.example .env
    echo ""
    echo "⚠️  IMPORTANT: Edit .env and add your API keys:"
    echo "   - ANTHROPIC_API_KEY (get from https://console.anthropic.com)"
    echo "   - SENDGRID_API_KEY (get from https://sendgrid.com)"
    echo "   - FROM_EMAIL (your verified SendGrid sender email)"
    echo "   - SECRET_KEY (generate a random string)"
    echo ""
fi

# Initialize database
echo "🗄️  Initializing database..."
python models.py

echo ""
echo "✨ Setup complete!"
echo ""
echo "Next steps:"
echo "1. Edit .env and add your API keys"
echo "2. Run: source venv/bin/activate"
echo "3. Run: python app.py"
echo "4. Visit: http://localhost:5000"
echo ""
echo "📚 See README.md for full documentation"
