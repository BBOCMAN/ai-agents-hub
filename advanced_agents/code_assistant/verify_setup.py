"""
Quick verification script to test Code Assistant setup
Run this to verify everything is working correctly
"""

import os
import sys
from pathlib import Path

def test_imports():
    """Test if all required modules can be imported"""
    print("🧪 Testing imports...")
    
    try:
        import langchain
        print("✅ LangChain imported successfully")
    except ImportError as e:
        print(f"❌ LangChain import failed: {e}")
        return False
    
    try:
        import langgraph
        print("✅ LangGraph imported successfully")
    except ImportError as e:
        print(f"❌ LangGraph import failed: {e}")
        return False
    
    try:
        import faiss
        print("✅ FAISS imported successfully")
    except ImportError as e:
        print(f"❌ FAISS import failed: {e}")
        return False
    
    try:
        from langchain_google_genai import ChatGoogleGenerativeAI
        print("✅ Google Generative AI imported successfully")
    except ImportError as e:
        print(f"❌ Google Generative AI import failed: {e}")
        return False
    
    return True

def test_environment():
    """Test environment configuration"""
    print("\n🔧 Testing environment...")
    
    try:
        from dotenv import load_dotenv
        load_dotenv()
        
        api_key = os.getenv("GOOGLE_API_KEY")
        if api_key:
            print("✅ GOOGLE_API_KEY found in environment")
            print(f"   Key preview: {api_key[:10]}***")
        else:
            print("⚠️ GOOGLE_API_KEY not found in .env file")
            print("   Please copy .env.example to .env and add your API key")
            return False
            
    except Exception as e:
        print(f"❌ Environment test failed: {e}")
        return False
    
    return True

def test_file_structure():
    """Test if all required files exist"""
    print("\n📁 Testing file structure...")
    
    required_files = [
        "main.py",
        "code_generator.py", 
        "document_loader.py",
        "validators.py",
        "config.py",
        "requirements.txt",
        ".env.example"
    ]
    
    missing_files = []
    for file in required_files:
        if Path(file).exists():
            print(f"✅ {file} found")
        else:
            print(f"❌ {file} missing")
            missing_files.append(file)
    
    if missing_files:
        print(f"\n⚠️ Missing files: {missing_files}")
        return False
    
    return True

def test_docs_directory():
    """Test if documentation files exist"""
    print("\n📚 Testing documentation...")
    
    docs_dir = Path("docs")
    if docs_dir.exists():
        doc_files = list(docs_dir.glob("*.txt"))
        if doc_files:
            print(f"✅ Found {len(doc_files)} documentation files")
            for doc in doc_files[:3]:  # Show first 3
                print(f"   📄 {doc.name}")
            if len(doc_files) > 3:
                print(f"   ... and {len(doc_files) - 3} more")
        else:
            print("⚠️ No .txt documentation files found")
            return False
    else:
        print("❌ docs/ directory not found")
        return False
    
    return True

def test_vector_store():
    """Test vector store directory"""
    print("\n🗂️ Testing vector store...")
    
    vector_dir = Path("vector_store")
    if vector_dir.exists():
        print("✅ vector_store/ directory exists")
        
        faiss_file = vector_dir / "index.faiss"
        pkl_file = vector_dir / "index.pkl"
        
        if faiss_file.exists() and pkl_file.exists():
            print("✅ Vector store files already exist")
            print(f"   📁 {faiss_file.name} ({faiss_file.stat().st_size} bytes)")
            print(f"   📁 {pkl_file.name} ({pkl_file.stat().st_size} bytes)")
        else:
            print("⚠️ Vector store files not found (run document_loader.py to create)")
    else:
        print("❌ vector_store/ directory not found")
        return False
    
    return True

def main():
    """Run all tests"""
    print("🚀 Code Assistant Setup Verification")
    print("=" * 50)
    
    tests = [
        ("Import Test", test_imports),
        ("Environment Test", test_environment), 
        ("File Structure Test", test_file_structure),
        ("Documentation Test", test_docs_directory),
        ("Vector Store Test", test_vector_store)
    ]
    
    results = []
    for test_name, test_func in tests:
        print(f"\n🧪 Running {test_name}...")
        try:
            result = test_func()
            results.append((test_name, result))
        except Exception as e:
            print(f"❌ {test_name} failed with exception: {e}")
            results.append((test_name, False))
    
    print("\n" + "=" * 50)
    print("📊 Test Results Summary:")
    print("=" * 50)
    
    passed = 0
    for test_name, result in results:
        status = "✅ PASS" if result else "❌ FAIL"
        print(f"{status} - {test_name}")
        if result:
            passed += 1
    
    print(f"\n🎯 {passed}/{len(tests)} tests passed")
    
    if passed == len(tests):
        print("\n🎉 All tests passed! Your Code Assistant is ready to use!")
        print("\n📖 Next steps:")
        print("1. Run: python document_loader.py  (if vector store not created)")
        print("2. Run: python main.py --help")
        print("3. Run: python main.py --interactive")
    else:
        print("\n⚠️ Some tests failed. Please check the issues above.")
        print("\n🔧 Common fixes:")
        print("1. Make sure virtual environment is activated")
        print("2. Copy .env.example to .env and add your API key")
        print("3. Run: pip install -r requirements.txt")

if __name__ == "__main__":
    main()
