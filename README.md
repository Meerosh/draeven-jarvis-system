# Draeven Jarvis System 🚀

**Your Complete AI Automation System for Business, E-Commerce, Email, Graphics & Coding**

> Built for **Meerosh** | Integrated with **Draeven HUD** | Multi-LLM Support (Ollama, ChatGPT, Claude, Gemini)

---

## ✨ What This Does

This is a **complete backend system** that powers your Draeven HUD with:

- ✅ **Smart AI Routing** - Uses cheap/free local LLM for simple tasks, saves expensive APIs for complex work
- ✅ **E-Commerce Automation** - Shopify & Etsy inventory sync, order processing, fulfillment
- ✅ **Email Management** - Automated sending, drafting, customer responses
- ✅ **Graphics Generation** - Create images, product cards, packaging designs
- ✅ **Code Generation** - Write, test, and execute code
- ✅ **CEO Dashboard** - You approve critical business decisions
- ✅ **Obsidian Integration** - Your knowledge vault becomes context for AI
- ✅ **Runs Locally** - No cloud, complete control, no data leaves your machine

---

## 🎯 Quick Start (Windows)

### **Step 1: Download the Repository**

**Option A - Super Easy (No Terminal Needed):**
1. Go to https://github.com/Meerosh/draeven-jarvis-system
2. Click the green **"Code"** button (top right)
3. Click **"Download ZIP"**
4. Right-click the ZIP → **"Extract All"**
5. Open the extracted folder

**Option B - Using Git (Slightly More Advanced):**
1. Open **PowerShell** (Windows key → type "powershell" → Enter)
2. Go to where you want it: `cd Desktop`
3. Copy and paste: `git clone https://github.com/Meerosh/draeven-jarvis-system.git`
4. Press Enter
5. When done: `cd draeven-jarvis-system`

### **Step 2: Run the System**

**Double-click this file:**
```
quick-start.bat
```

That's it! Everything else happens automatically.

### **Step 3: Point Draeven at Your Jarvis**

See `gui-integration/DRAEVEN_SETUP.md` for the exact code change.

---

## 📋 What's in This Repo?

```
draeven-jarvis-system/
│
├── README.md                           ← You are here
├── SETUP_GUIDE.md                      ← Step-by-step walkthrough
├── TROUBLESHOOTING.md                  ← If something breaks
│
├── quick-start.bat                     ← Windows: Double-click this!
├── docker-compose.yml                  ← Runs all the services
├── .env.example                        ← Copy to .env, add your API keys
│
├── config/
│   ├── jarvis-config.yaml              ← Main settings
│   ├── agents-config.yaml              ← Agent definitions
│   └── llm-routing.yaml                ← Multi-LLM smart routing
│
├── agents/
│   ├── inventory-agent.py              ← Shopify/Etsy sync
│   ├── email-agent.py                  ← Email automation
│   ├── graphics-agent.py               ← Image generation
│   ├── coding-agent.py                 ← Code generation/execution
│   ├── order-processor.py              ← Order fulfillment
│   └── router-agent.py                 ← Smart LLM routing
│
├── api/
│   ├── server.py                       ← FastAPI backend
│   ├── routes.py                       ← API endpoints
│   └── middleware.py                   ← Request handling
│
├── gui-integration/
│   ├── DRAEVEN_SETUP.md                ← How to integrate with Draeven
│   ├── draeven-integration.js          ← Copy this into your Draeven code
│   └── example-api-calls.js            ← Example requests
│
├── obsidian-integration/
│   ├── setup.md                        ← Connect your Obsidian vault
│   └── vault-loader.py                 ← Loads your notes as context
│
├── requirements.txt                    ← Python packages needed
├── Dockerfile                          ← Docker container setup
└── .gitignore                          ← Files not to upload
```

---

## 🏗️ Architecture

```
Your Draeven HUD (unchanged!)
        ↓
    API Request
        ↓
Jarvis Backend (FastAPI)
        ↓
   Router Agent
   (smart LLM picker)
        ↓
    ┌───┴───┬───────┬─────────┐
    ↓       ↓       ↓         ↓
  Ollama  ChatGPT Claude   Gemini
  (local) (paid)  (paid)   (free)
    ↓       ↓       ↓         ↓
    └───┬───┴───────┴─────────┘
        ↓
   Response → Draeven HUD
```

---

## 📝 Prerequisites

You already have most of this:

- ✅ **Windows** (you got it)
- ✅ **Docker** (you got it)
- ✅ **Ollama** (you got it - local LLM)
- ⚠️ **API Keys** (we'll set this up):
  - ChatGPT Plus account (your API key)
  - Claude Pro account (your API key)
  - Gemini account (your API key)
  - Shopify store (optional, for e-commerce)
  - Etsy shop (optional, for e-commerce)

---

## 🚀 Next Steps

1. **Download the repo** (see Quick Start above)
2. **Follow SETUP_GUIDE.md** (step-by-step)
3. **Read gui-integration/DRAEVEN_SETUP.md** (integrate Draeven)
4. **Run quick-start.bat** (launch everything)
5. **Update your Draeven HUD** (3 lines of code)
6. **Test it** (ask Draeven a question!)

---

## 🔧 Configuration

### **1. Set Your API Keys**

Copy the example file:
```bash
copy .env.example .env
```

Open `.env` and add your keys:
```
OPENAI_API_KEY=sk-your-key-here
ANTHROPIC_API_KEY=sk-ant-your-key-here
GOOGLE_API_KEY=your-gemini-key
```

### **2. Choose Your LLMs**

Edit `config/llm-routing.yaml`:
```yaml
default_llm: ollama              # Use local Ollama by default
fallback_to_chatgpt_when: "task_complexity > 7"
fallback_to_claude_when: "context_length > 50000"
```

### **3. Connect Obsidian (Optional)**

Edit `config/jarvis-config.yaml`:
```yaml
obsidian:
  vault_path: "C:\\Users\\YourName\\Documents\\ObsidianVault"
  enabled: true
```

---

## 🎮 Using Your Jarvis

### **Via Draeven HUD**

Your HUD now talks to Jarvis instead of ChatGPT:

```javascript
// Instead of sending to OpenAI
// Just send to your local Jarvis
const response = await fetch("http://localhost:8000/api/chat", {
  method: "POST",
  body: JSON.stringify({ message: userInput })
});
```

### **Example Queries**

**Business:**
- "What's my total inventory across Shopify and Etsy?"
- "Process all pending orders and flag high-value ones"
- "Send welcome email to new customers"

**E-Commerce:**
- "Sync inventory between Shopify and Etsy"
- "Generate 5 product descriptions for new items"
- "Check order fulfillment status"

**Creative:**
- "Generate a product card image for Widget A"
- "Create a marketing email template"
- "Design packaging label for my products"

**Coding:**
- "Write a Python script to backup my database"
- "Generate API documentation for my store"
- "Create a webhook handler for new orders"

---

## 📊 Token Saving Strategy

| Task | Default LLM | Cost | Tokens Used |
|------|-------------|------|-------------|
| Simple question | Ollama | $0 | ∞ (unlimited) |
| Inventory check | Ollama | $0 | ∞ (unlimited) |
| Email draft | ChatGPT | $0.02 | ~500 |
| Large document | Claude | $0 (included) | ~100K |
| Creative idea | Gemini | $0 | ∞ (free tier) |

**Result:** Save $50-100/month on API costs while getting unlimited capability!

---

## 🆘 Need Help?

1. **Setup issues?** → Read `SETUP_GUIDE.md`
2. **Something broke?** → Check `TROUBLESHOOTING.md`
3. **Draeven integration?** → See `gui-integration/DRAEVEN_SETUP.md`
4. **Obsidian setup?** → See `obsidian-integration/setup.md`

---

## 🤝 Support

- Your Jarvis system runs **100% locally**
- All data stays on **your machine**
- You control **all API keys**
- No subscription needed
- Modify code however you want

---

## 📄 License

MIT License - Do whatever you want with this code!

---

**Made with ❤️ for Meerosh's Draeven System**

Ready to transform your business? Let's go! 🚀
