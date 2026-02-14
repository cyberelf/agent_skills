#!/bin/bash
# Setup OpenSpec and install common skills
# Usage: ./setup.sh <workspace-path> [skill1] [skill2] ...

set -e

WORKSPACE="${1:-.}"
shift
SKILLS=("$@")

cd "$WORKSPACE"

echo "🏗️  Setting up OpenSpec in: $(pwd)"
echo ""

# Install OpenSpec
echo "📦 Installing OpenSpec..."
if openspec init --tools claude; then
  echo "✅ OpenSpec installed"
else
  echo "❌ OpenSpec installation failed"
  exit 1
fi

echo ""

# Install skills if provided
if [ ${#SKILLS[@]} -gt 0 ]; then
  echo "📚 Installing skills:"
  for skill in "${SKILLS[@]}"; do
    echo "   - $skill"
    if npx skills add cyberelf/agent_skills --skill "$skill" --agent all -y; then
      echo "     ✅ Installed"
    else
      echo "     ⚠️  Failed"
    fi
  done
else
  echo "ℹ️  No skills specified. Common skills:"
  echo "   - api-development"
  echo "   - debugging"
  echo "   - test-automation"
  echo "   - ui-components"
  echo "   - database-design"
  echo ""
  echo "   Install with: npx skills add cyberelf/agent_skills --skill <name> --agent all -y"
fi

echo ""
echo "✅ Setup complete!"
echo ""
echo "📝 Next steps:"
echo "   1. Create requirements.md with your requirements"
echo "   2. Run: ./delegate.sh <change-name> [max-turns]"
