# Learning Addon - Simple Odoo Development Tutorial

This is a simple Odoo addon designed to help you learn the basics of Odoo development. It demonstrates:

- Creating custom models with various field types
- Building backend views (tree, form, menu)
- Website integration with public pages
- Security configuration
- Demo data creation

## What This Addon Does

The Learning Addon creates a simple learning tracker system where you can:

1. **Backend Features:**
   - Create and manage learning records
   - Track learning progress with categories and difficulty levels
   - Mark items as completed with completion dates
   - Add notes and descriptions

2. **Website Features:**
   - Public page showing all learning records at `/learning`
   - Individual record detail pages
   - Responsive design with Bootstrap styling
   - Automatic menu item in website navigation

## Installation Instructions

### Prerequisites
- Docker and Docker Compose installed
- This Odoo repository cloned locally

### Step 1: Start Odoo
```bash
cd /path/to/odoo/repository
docker-compose -f docker-compose-local.yml up -d
```

Wait for Odoo to start (usually takes 30-60 seconds). You can check the logs:
```bash
docker logs odoo-odoo-1 -f
```

### Step 2: Access Odoo
1. Open your browser and go to `http://localhost:8069`
2. Create a new database or use an existing one
3. Make sure to enable "Developer Mode" from the Settings menu

### Step 3: Install the Learning Addon
1. Go to Apps menu in Odoo
2. Click "Update Apps List" (you may need to enable developer mode first)
3. Search for "Learning Addon"
4. Click "Activate" to install the module

### Step 4: Use the Backend Features
1. After installation, you'll see a new "Learning Tracker" menu in the main navigation
2. Click on "Learning Records" to see the demo data
3. Create new learning records using the "Create" button
4. Try editing existing records to see all the fields

### Step 5: Test Website Integration
1. Go to your website (click the "Website" app or visit the frontend)
2. You'll see a "Learning" menu item in the top navigation
3. Click it to see all learning records displayed publicly
4. Click on individual records to see their details

## File Structure Explanation

```
learning_addon/
├── __init__.py                 # Module initialization
├── __manifest__.py            # Module metadata and dependencies
├── README.md                  # This file
├── models/
│   ├── __init__.py           # Models initialization
│   └── learning_record.py    # Main model definition
├── views/
│   ├── learning_views.xml    # Backend views (tree, form, menu)
│   └── website_templates.xml # Website templates
├── controllers/
│   ├── __init__.py           # Controllers initialization
│   └── main.py               # Website route handlers
├── security/
│   └── ir.model.access.csv   # Access rights configuration
└── data/
    └── demo_data.xml         # Sample data for testing
```

## Key Learning Points

### 1. Model Definition (`models/learning_record.py`)
- Shows how to create a custom model inheriting from `models.Model`
- Demonstrates various field types: Char, Text, Selection, Boolean, Date, Html
- Includes an `@api.onchange` method for dynamic field updates

### 2. Views (`views/learning_views.xml`)
- Tree view for list display
- Form view with groups and notebook pages
- Action and menu definitions
- Help text for empty states

### 3. Website Integration (`controllers/main.py` + `views/website_templates.xml`)
- HTTP routes with public authentication
- Template rendering with context data
- Bootstrap-styled responsive templates
- Website menu integration

### 4. Security (`security/ir.model.access.csv`)
- Public read access for website display
- User permissions for backend management

### 5. Demo Data (`data/demo_data.xml`)
- Sample records with various field combinations
- HTML content in notes field
- Different completion states

## Customization Ideas

Once you understand this addon, try these modifications:

1. **Add new fields** to the learning_record model
2. **Create new views** (kanban, calendar, graph)
3. **Add more website pages** with different layouts
4. **Implement search and filtering** on the website
5. **Add user-specific records** (remove sudo() and add user filtering)
6. **Create reports** using Odoo's reporting system
7. **Add email notifications** when records are completed

## Troubleshooting

### Module Not Appearing in Apps List
1. Make sure you clicked "Update Apps List" in developer mode
2. Check the Odoo logs for any errors: `docker logs odoo-odoo-1`
3. Verify all files are present in the `addons/learning_addon/` directory

### Installation Errors
1. Check the syntax of all XML files
2. Ensure all Python files have proper indentation
3. Verify the `__manifest__.py` dependencies are correct

### Website Pages Not Working
1. Make sure the Website app is installed
2. Check that controllers are properly imported in `__init__.py`
3. Verify template names match between controllers and XML files

## Next Steps

After mastering this simple addon, you can:

1. Study the official Odoo documentation
2. Explore more complex field types and relationships
3. Learn about workflows and automated actions
4. Dive into advanced website features
5. Understand Odoo's ORM and database operations

Happy learning! 🚀
