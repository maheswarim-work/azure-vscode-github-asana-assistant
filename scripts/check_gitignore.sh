#!/bin/bash

# Script to verify that sensitive files are properly ignored by git

echo "🔍 Checking gitignore protection for sensitive files..."
echo "======================================================="
echo ""

# Check if .env file is ignored
if git check-ignore .env >/dev/null 2>&1; then
    echo "✅ .env file is properly ignored"
else
    echo "❌ WARNING: .env file is NOT ignored!"
fi

# Check if azure_config.env is ignored
if git check-ignore azure_config.env >/dev/null 2>&1; then
    echo "✅ azure_config.env is properly ignored"
else
    echo "❌ WARNING: azure_config.env is NOT ignored!"
fi

# Check for any sensitive files that might be tracked
echo ""
echo "🔍 Checking for potentially sensitive files in git..."

SENSITIVE_FILES=$(git ls-files | grep -E '\.(env|key|pem|p12|pfx|credentials)$|secrets\.json|azure_config' | grep -v '.env.example')

if [ -z "$SENSITIVE_FILES" ]; then
    echo "✅ No sensitive files found in git tracking"
else
    echo "❌ WARNING: Found potentially sensitive files in git:"
    echo "$SENSITIVE_FILES"
fi

# Show what environment files exist but are ignored
echo ""
echo "📁 Environment files in project:"
find . -maxdepth 1 -name "*.env*" -type f | while read file; do
    if git check-ignore "$file" >/dev/null 2>&1; then
        echo "✅ $file (ignored)"
    elif [[ "$file" == *".env.example" ]]; then
        echo "✅ $file (template - tracked as intended)"
    else
        echo "❌ $file (NOT IGNORED - DANGER!)"
    fi
done

echo ""
echo "🔒 Security Status:"
if [ -z "$SENSITIVE_FILES" ]; then
    echo "✅ All sensitive files are properly protected"
    echo "✅ Safe to commit and push to repository"
else
    echo "❌ SECURITY RISK: Sensitive files detected in git"
    echo "❌ DO NOT commit until this is resolved"
fi

echo ""
echo "💡 If you see any warnings:"
echo "   1. Remove sensitive files from git: git rm --cached <filename>"
echo "   2. Make sure .gitignore includes the pattern"
echo "   3. Commit the .gitignore changes"
echo "   4. Re-run this script to verify"