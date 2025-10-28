#!/usr/bin/env python3
"""
Quick Setup Script for News Screener Integration
Run this to set up the news screener in your existing project
"""

import os
import sys
import shutil
from pathlib import Path

def print_header(text):
    print("\n" + "="*70)
    print(f"  {text}")
    print("="*70 + "\n")

def check_dependencies():
    """Check if required packages are installed"""
    print_header("Checking Dependencies")
    
    required_packages = [
        ('flask', 'Flask'),
        ('fyers_apiv3', 'fyers-apiv3'),
        ('pandas', 'pandas'),
        ('numpy', 'numpy'),
        ('requests', 'requests'),
    ]
    
    missing = []
    for module, package in required_packages:
        try:
            __import__(module)
            print(f"✓ {package} installed")
        except ImportError:
            print(f"✗ {package} missing")
            missing.append(package)
    
    if missing:
        print(f"\n⚠️  Missing packages: {', '.join(missing)}")
        print("Run: pip install " + " ".join(missing))
        return False
    
    print("\n✓ All dependencies installed!")
    return True

def check_project_structure():
    """Verify project structure"""
    print_header("Checking Project Structure")
    
    required_dirs = ['bot_core', 'templates', 'auth']
    optional_dirs = ['static', 'utils']
    
    for dir_name in required_dirs:
        if os.path.exists(dir_name):
            print(f"✓ {dir_name}/ exists")
        else:
            print(f"✗ {dir_name}/ missing - creating...")
            os.makedirs(dir_name)
            # Create __init__.py for Python packages
            if dir_name in ['bot_core', 'auth', 'utils']:
                Path(f"{dir_name}/__init__.py").touch()
    
    for dir_name in optional_dirs:
        if os.path.exists(dir_name):
            print(f"✓ {dir_name}/ exists")
        else:
            print(f"ℹ️  {dir_name}/ not found (optional)")
    
    return True

def check_env_file():
    """Check and update .env file"""
    print_header("Checking Environment Configuration")
    
    env_path = Path('.env')
    
    if not env_path.exists():
        print("✗ .env file not found")
        create = input("Create .env file? (y/n): ").lower()
        if create == 'y':
            env_path.touch()
            print("✓ Created .env file")
        else:
            print("⚠️  You'll need to create .env manually")
            return False
    else:
        print("✓ .env file exists")
    
    # Check for required variables
    required_vars = [
        'FYERS_CLIENT_ID',
        'FYERS_SECRET_KEY',
        'FYERS_ACCESS_TOKEN',
        'NEWS_API_KEY',
        'SECRET_KEY'
    ]
    
    screener_vars = [
        'VOLUME_SURGE_THRESHOLD=2.0',
        'PRICE_CHANGE_MIN=3.0',
        'PRICE_CHANGE_MAX=15.0',
        'LOOKBACK_DAYS=5',
        'MIN_PRICE=20',
        'MAX_PRICE=5000'
    ]
    
    with open(env_path, 'r') as f:
        env_content = f.read()
    
    missing_vars = []
    for var in required_vars:
        if var not in env_content:
            missing_vars.append(var)
            print(f"✗ {var} not found")
        else:
            print(f"✓ {var} configured")
    
    # Add screener-specific variables if missing
    needs_update = False
    for var in screener_vars:
        if var.split('=')[0] not in env_content:
            needs_update = True
            break
    
    if needs_update:
        print("\n📝 Adding news screener configuration to .env...")
        with open(env_path, 'a') as f:
            f.write("\n\n# News Screener Configuration\n")
            for var in screener_vars:
                f.write(f"{var}\n")
        print("✓ Added screener configuration")
    
    if missing_vars:
        print(f"\n⚠️  Missing variables: {', '.join(missing_vars)}")
        print("Please add them to your .env file")
        return False
    
    return True

def create_screener_files():
    """Guide user to create screener files"""
    print_header("Setting Up Screener Files")
    
    files_to_create = {
        'bot_core/news_screener.py': 'Main news screener class',
        'bot_core/enhanced_screener.py': 'Advanced analysis features',
        'bot_core/fyers_auth.py': 'Authentication helper',
        'templates/screener.html': 'Screener dashboard UI'
    }
    
    for filepath, description in files_to_create.items():
        if os.path.exists(filepath):
            print(f"✓ {filepath} exists - {description}")
        else:
            print(f"✗ {filepath} missing - {description}")
            print(f"   Create this file and paste the content from the artifact")
    
    print("\n📚 Refer to the Project Structure Guide for file contents")
    return True

def update_init_files():
    """Update __init__.py files for proper imports"""
    print_header("Updating Import Configuration")
    
    bot_core_init = Path('bot_core/__init__.py')
    
    if bot_core_init.exists():
        with open(bot_core_init, 'r') as f:
            content = f.read()
        
        if 'FyersNewsScreener' not in content:
            print("📝 Adding screener imports to bot_core/__init__.py...")
            
            imports_to_add = """
# News Screener imports
try:
    from .news_screener import FyersNewsScreener
    from .enhanced_screener import NewsAnalyzer, AdvancedFilters, get_trading_recommendation
    SCREENER_AVAILABLE = True
except ImportError as e:
    print(f"Screener not available: {e}")
    SCREENER_AVAILABLE = False
    FyersNewsScreener = None
    NewsAnalyzer = None
    AdvancedFilters = None
    get_trading_recommendation = None

__all__ = [
    'broker', 
    'active_positions',
    'FyersNewsScreener',
    'NewsAnalyzer',
    'AdvancedFilters',
    'get_trading_recommendation',
    'SCREENER_AVAILABLE'
]
"""
            with open(bot_core_init, 'a') as f:
                f.write(imports_to_add)
            
            print("✓ Updated bot_core/__init__.py")
        else:
            print("✓ bot_core/__init__.py already configured")
    else:
        print("⚠️  bot_core/__init__.py not found")
        bot_core_init.touch()
        print("✓ Created bot_core/__init__.py")
    
    return True

def test_imports():
    """Test if screener can be imported"""
    print_header("Testing Imports")
    
    try:
        sys.path.insert(0, os.getcwd())
        
        print("Testing bot_core imports...")
        from bot_core import SCREENER_AVAILABLE
        
        if SCREENER_AVAILABLE:
            from bot_core import FyersNewsScreener, NewsAnalyzer, AdvancedFilters
            print("✓ All screener imports successful!")
            return True
        else:
            print("⚠️  Screener imports not available")
            print("   Make sure news_screener.py and enhanced_screener.py are in bot_core/")
            return False
            
    except ImportError as e:
        print(f"✗ Import error: {e}")
        print("   Check that all screener files are properly created")
        return False

def show_next_steps():
    """Display next steps for user"""
    print_header("Setup Complete! Next Steps")
    
    print("1. 🔐 Authenticate with Fyers:")
    print("   python bot_core/fyers_auth.py")
    print()
    print("2. 🗝️  Get NewsAPI key:")
    print("   Visit: https://newsapi.org/register")
    print("   Add to .env: NEWS_API_KEY=your_key_here")
    print()
    print("3. 🚀 Start the application:")
    print("   python app.py")
    print()
    print("4. 🌐 Access dashboards:")
    print("   Trading Bot:   http://localhost:5000/dashboard")
    print("   News Screener: http://localhost:5000/screener")
    print()
    print("5. 📊 Test the screener:")
    print("   - Login at http://localhost:5000/login")
    print("   - Navigate to screener dashboard")
    print("   - Click 'Start Scan'")
    print()
    print("6. 📖 Read the documentation:")
    print("   Check README.md for detailed usage guide")
    print()
    print("=" * 70)
    print("Need help? Check the Project Structure Guide artifact!")
    print("=" * 70)

def main():
    """Main setup function"""
    print("""
    ╔══════════════════════════════════════════════════════════════╗
    ║                                                              ║
    ║          NEWS SCREENER SETUP HELPER                          ║
    ║          Quick integration for your trading bot              ║
    ║                                                              ║
    ╚══════════════════════════════════════════════════════════════╝
    """)
    
    # Run checks
    steps = [
        ("Checking Dependencies", check_dependencies),
        ("Verifying Project Structure", check_project_structure),
        ("Checking Environment File", check_env_file),
        ("Setting Up Screener Files", create_screener_files),
        ("Updating Import Configuration", update_init_files),
        ("Testing Imports", test_imports),
    ]
    
    all_passed = True
    for step_name, step_func in steps:
        result = step_func()
        if not result:
            all_passed = False
            print(f"\n⚠️  {step_name} had issues. Please fix them before continuing.\n")
    
    if all_passed:
        print("\n" + "🎉" * 35)
        print("ALL CHECKS PASSED!")
        print("🎉" * 35)
        show_next_steps()
    else:
        print("\n" + "⚠️ " * 25)
        print("SOME CHECKS FAILED - Please address the issues above")
        print("⚠️ " * 25)
        print("\nCommon issues:")
        print("- Missing Python packages: pip install -r requirements.txt")
        print("- Missing screener files: Copy from artifacts to proper directories")
        print("- Missing .env variables: Add required keys to .env file")

if __name__ == "__main__":
    main()