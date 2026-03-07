#!/usr/bin/env python3
"""
Generate an interactive website for exploring five-county local government data.
Creates a comprehensive web interface for reporters to explore issues, budgets, schools, etc.
"""

import json
from pathlib import Path
from datetime import datetime
import shutil

# Base directory
BASE_DIR = Path(__file__).parent
DATA_DIR = BASE_DIR / "scraped_county_data"
OUTPUT_DIR = BASE_DIR / "website"

# Counties to process
COUNTIES = ["caroline", "dorchester", "kent", "queen_annes", "talbot"]

# County name mapping
COUNTY_NAMES = {
    "caroline": "Caroline County",
    "dorchester": "Dorchester County",
    "kent": "Kent County",
    "queen_annes": "Queen Anne's County",
    "talbot": "Talbot County"
}


def load_json_file(filepath: Path) -> dict | list:
    """Load JSON content from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return json.load(f)
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return {}


def load_file_content(filepath: Path) -> str:
    """Load content from a file."""
    try:
        with open(filepath, 'r', encoding='utf-8') as f:
            return f.read()
    except Exception as e:
        print(f"Warning: Could not load {filepath}: {e}")
        return ""


def create_directory_structure():
    """Create the website directory structure."""
    OUTPUT_DIR.mkdir(exist_ok=True)
    (OUTPUT_DIR / "data").mkdir(exist_ok=True)
    (OUTPUT_DIR / "css").mkdir(exist_ok=True)
    (OUTPUT_DIR / "js").mkdir(exist_ok=True)


def generate_main_css():
    """Generate the main CSS file."""
    css_content = """
/* Reset and Base Styles */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
}

:root {
    --primary-color: #2c3e50;
    --secondary-color: #3498db;
    --accent-color: #e74c3c;
    --success-color: #27ae60;
    --warning-color: #f39c12;
    --light-bg: #ecf0f1;
    --dark-bg: #34495e;
    --text-color: #2c3e50;
    --border-color: #bdc3c7;
    --shadow: 0 2px 4px rgba(0,0,0,0.1);
}

body {
    font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Helvetica Neue", Arial, sans-serif;
    line-height: 1.6;
    color: var(--text-color);
    background-color: #fff;
}

/* Header */
header {
    background: linear-gradient(135deg, var(--primary-color) 0%, var(--dark-bg) 100%);
    color: white;
    padding: 1.5rem 0;
    box-shadow: 0 2px 10px rgba(0,0,0,0.2);
}

header .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

header h1 {
    font-size: 2rem;
    margin-bottom: 0.5rem;
    font-weight: 700;
}

header p {
    opacity: 0.9;
    font-size: 1rem;
}

/* Navigation */
nav {
    background-color: white;
    box-shadow: var(--shadow);
    position: sticky;
    top: 0;
    z-index: 100;
}

nav .container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 0 2rem;
}

nav ul {
    list-style: none;
    display: flex;
    flex-wrap: wrap;
}

nav li {
    margin-right: 0.5rem;
}

nav a {
    display: block;
    padding: 1rem 1.5rem;
    text-decoration: none;
    color: var(--text-color);
    font-weight: 500;
    transition: all 0.3s ease;
    border-bottom: 3px solid transparent;
}

nav a:hover {
    background-color: var(--light-bg);
    border-bottom-color: var(--secondary-color);
}

nav a.active {
    color: var(--secondary-color);
    border-bottom-color: var(--secondary-color);
}

/* Container */
.container {
    max-width: 1200px;
    margin: 0 auto;
    padding: 2rem;
}

/* Cards */
.card {
    background: white;
    border-radius: 8px;
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    box-shadow: var(--shadow);
    transition: transform 0.3s ease, box-shadow 0.3s ease;
}

.card:hover {
    transform: translateY(-2px);
    box-shadow: 0 4px 12px rgba(0,0,0,0.15);
}

.card h2 {
    color: var(--primary-color);
    margin-bottom: 1rem;
    font-size: 1.5rem;
    border-bottom: 2px solid var(--secondary-color);
    padding-bottom: 0.5rem;
}

.card h3 {
    color: var(--primary-color);
    margin-top: 1rem;
    margin-bottom: 0.5rem;
    font-size: 1.2rem;
}

/* Grid System */
.grid {
    display: grid;
    gap: 1.5rem;
    margin-bottom: 2rem;
}

.grid-2 {
    grid-template-columns: repeat(auto-fit, minmax(300px, 1fr));
}

.grid-3 {
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
}

/* Stats */
.stat-box {
    background: linear-gradient(135deg, var(--secondary-color) 0%, #2980b9 100%);
    color: white;
    padding: 1.5rem;
    border-radius: 8px;
    text-align: center;
    box-shadow: var(--shadow);
}

.stat-box .number {
    font-size: 2.5rem;
    font-weight: bold;
    margin-bottom: 0.5rem;
}

.stat-box .label {
    font-size: 1rem;
    opacity: 0.9;
}

/* Tabs */
.tabs {
    display: flex;
    border-bottom: 2px solid var(--border-color);
    margin-bottom: 1.5rem;
    flex-wrap: wrap;
}

.tab {
    padding: 1rem 1.5rem;
    cursor: pointer;
    border: none;
    background: none;
    color: var(--text-color);
    font-size: 1rem;
    font-weight: 500;
    transition: all 0.3s ease;
    border-bottom: 3px solid transparent;
    margin-bottom: -2px;
}

.tab:hover {
    background-color: var(--light-bg);
}

.tab.active {
    color: var(--secondary-color);
    border-bottom-color: var(--secondary-color);
}

.tab-content {
    display: none;
}

.tab-content.active {
    display: block;
    animation: fadeIn 0.3s ease;
}

@keyframes fadeIn {
    from { opacity: 0; }
    to { opacity: 1; }
}

/* Tables */
table {
    width: 100%;
    border-collapse: collapse;
    margin: 1rem 0;
    background: white;
}

table th {
    background-color: var(--primary-color);
    color: white;
    padding: 0.75rem;
    text-align: left;
    font-weight: 600;
}

table td {
    padding: 0.75rem;
    border-bottom: 1px solid var(--border-color);
}

table tr:hover {
    background-color: var(--light-bg);
}

/* Search and Filters */
.search-box {
    margin-bottom: 1.5rem;
}

.search-box input {
    width: 100%;
    padding: 0.75rem 1rem;
    font-size: 1rem;
    border: 2px solid var(--border-color);
    border-radius: 8px;
    transition: border-color 0.3s ease;
}

.search-box input:focus {
    outline: none;
    border-color: var(--secondary-color);
}

/* Tags */
.tag {
    display: inline-block;
    padding: 0.25rem 0.75rem;
    background-color: var(--secondary-color);
    color: white;
    border-radius: 20px;
    font-size: 0.875rem;
    margin-right: 0.5rem;
    margin-bottom: 0.5rem;
}

.tag.governance { background-color: #3498db; }
.tag.budget { background-color: #27ae60; }
.tag.infrastructure { background-color: #f39c12; }
.tag.education { background-color: #9b59b6; }
.tag.environment { background-color: #16a085; }
.tag.safety { background-color: #e74c3c; }

/* Issue Cards */
.issue-card {
    border-left: 4px solid var(--secondary-color);
    padding-left: 1rem;
    margin-bottom: 1rem;
}

.issue-card h4 {
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.issue-card .meta {
    color: #7f8c8d;
    font-size: 0.875rem;
    margin-bottom: 0.5rem;
}

/* Story List */
.story-item {
    padding: 1rem;
    border-bottom: 1px solid var(--border-color);
}

.story-item:last-child {
    border-bottom: none;
}

.story-item h4 {
    color: var(--primary-color);
    margin-bottom: 0.5rem;
}

.story-item .date {
    color: #7f8c8d;
    font-size: 0.875rem;
}

/* Loading State */
.loading {
    text-align: center;
    padding: 3rem;
    color: #7f8c8d;
}

/* Footer */
footer {
    background-color: var(--primary-color);
    color: white;
    text-align: center;
    padding: 2rem;
    margin-top: 4rem;
}

footer p {
    opacity: 0.9;
}

/* Responsive Design */
@media (max-width: 768px) {
    header h1 {
        font-size: 1.5rem;
    }
    
    nav ul {
        flex-direction: column;
    }
    
    nav li {
        margin-right: 0;
    }
    
    .container {
        padding: 1rem;
    }
    
    .grid-2, .grid-3 {
        grid-template-columns: 1fr;
    }
}

/* Utilities */
.mb-1 { margin-bottom: 0.5rem; }
.mb-2 { margin-bottom: 1rem; }
.mb-3 { margin-bottom: 1.5rem; }
.mt-1 { margin-top: 0.5rem; }
.mt-2 { margin-top: 1rem; }
.mt-3 { margin-top: 1.5rem; }

.text-center { text-align: center; }
.text-muted { color: #7f8c8d; }
.text-small { font-size: 0.875rem; }
"""
    
    with open(OUTPUT_DIR / "css" / "style.css", 'w') as f:
        f.write(css_content)


def generate_main_js():
    """Generate the main JavaScript file."""
    js_content = """
// Global data storage
let countyData = {};
let storiesData = [];
let currentCounty = 'caroline';

// Initialize the application
document.addEventListener('DOMContentLoaded', function() {
    loadAllData();
    setupEventListeners();
});

// Load all data files
async function loadAllData() {
    try {
        // Load stories
        const storiesResponse = await fetch('data/stories.json');
        storiesData = await storiesResponse.json();
        
        // Load county data
        for (const county of ['caroline', 'dorchester', 'kent', 'queen_annes', 'talbot']) {
            const response = await fetch(`data/${county}_data.json`);
            countyData[county] = await response.json();
        }
        
        // Initialize the overview page
        renderOverview();
    } catch (error) {
        console.error('Error loading data:', error);
        document.body.innerHTML = '<div class="container"><div class="card"><h2>Error Loading Data</h2><p>Could not load data files. Please check the console for details.</p></div></div>';
    }
}

// Setup event listeners
function setupEventListeners() {
    // Navigation
    document.querySelectorAll('nav a').forEach(link => {
        link.addEventListener('click', function(e) {
            e.preventDefault();
            const page = this.getAttribute('data-page');
            const county = this.getAttribute('data-county');
            
            // Update active nav
            document.querySelectorAll('nav a').forEach(a => a.classList.remove('active'));
            this.classList.add('active');
            
            // Render appropriate page
            if (page === 'overview') {
                renderOverview();
            } else if (county) {
                currentCounty = county;
                renderCountyPage(county);
            }
        });
    });
}

// Render overview page
function renderOverview() {
    const content = document.getElementById('content');
    
    let html = '<div class="container">';
    html += '<h1 class="mb-3">Five-County Overview</h1>';
    
    // Stats grid
    html += '<div class="grid grid-3 mb-3">';
    html += `<div class="stat-box"><div class="number">5</div><div class="label">Counties</div></div>`;
    html += `<div class="stat-box"><div class="number">${storiesData.length}</div><div class="label">Stories Analyzed</div></div>`;
    html += `<div class="stat-box"><div class="number">${Object.keys(countyData).length}</div><div class="label">Data Sources</div></div>`;
    html += '</div>';
    
    // Regional issues
    html += '<div class="card">';
    html += '<h2>Cross-County Issues</h2>';
    
    // Get top issues from stories
    const issueCounts = {};
    storiesData.forEach(story => {
        const tag = story.beatbook_tag || 'Other';
        issueCounts[tag] = (issueCounts[tag] || 0) + 1;
    });
    
    const topIssues = Object.entries(issueCounts)
        .sort((a, b) => b[1] - a[1])
        .slice(0, 10);
    
    html += '<div class="grid grid-2">';
    topIssues.forEach(([issue, count]) => {
        html += `<div class="issue-card">`;
        html += `<h4>${issue}</h4>`;
        html += `<div class="meta">${count} stories across all counties</div>`;
        html += `</div>`;
    });
    html += '</div>';
    html += '</div>';
    
    // County quick links
    html += '<div class="card">';
    html += '<h2>Select a County</h2>';
    html += '<div class="grid grid-2">';
    
    for (const [key, name] of Object.entries({
        'caroline': 'Caroline County',
        'dorchester': 'Dorchester County',
        'kent': 'Kent County',
        'queen_annes': "Queen Anne's County",
        'talbot': 'Talbot County'
    })) {
        const data = countyData[key];
        const pop = data?.census?.total_population || 'N/A';
        html += `<div class="card" onclick="navigateToCounty('${key}')" style="cursor: pointer;">`;
        html += `<h3>${name}</h3>`;
        html += `<p class="text-muted">Population: ${typeof pop === 'number' ? pop.toLocaleString() : pop}</p>`;
        html += `<p class="text-small mt-2">Click to explore →</p>`;
        html += `</div>`;
    }
    
    html += '</div>';
    html += '</div>';
    
    html += '</div>';
    content.innerHTML = html;
}

// Navigate to county
function navigateToCounty(county) {
    document.querySelector(`nav a[data-county="${county}"]`).click();
}

// Render county page
function renderCountyPage(county) {
    const content = document.getElementById('content');
    const data = countyData[county];
    const countyName = {
        'caroline': 'Caroline County',
        'dorchester': 'Dorchester County',
        'kent': 'Kent County',
        'queen_annes': "Queen Anne's County",
        'talbot': 'Talbot County'
    }[county];
    
    let html = '<div class="container">';
    html += `<h1 class="mb-3">${countyName}</h1>`;
    
    // Tabs
    html += '<div class="tabs">';
    html += '<button class="tab active" onclick="showTab(\'summary\')">Summary</button>';
    html += '<button class="tab" onclick="showTab(\'government\')">Government</button>';
    html += '<button class="tab" onclick="showTab(\'issues\')">Key Issues</button>';
    html += '<button class="tab" onclick="showTab(\'budget\')">Budget</button>';
    html += '<button class="tab" onclick="showTab(\'schools\')">Schools</button>';
    html += '<button class="tab" onclick="showTab(\'stories\')">News Stories</button>';
    html += '</div>';
    
    // Tab contents
    html += renderSummaryTab(county, data, countyName);
    html += renderGovernmentTab(county, data);
    html += renderIssuesTab(county, data, countyName);
    html += renderBudgetTab(county, data);
    html += renderSchoolsTab(county, data);
    html += renderStoriesTab(county, countyName);
    
    html += '</div>';
    content.innerHTML = html;
}

// Render summary tab
function renderSummaryTab(county, data, countyName) {
    let html = '<div class="tab-content active" id="summary">';
    
    // Quick stats
    html += '<div class="grid grid-3 mb-3">';
    if (data.census) {
        const pop = data.census.total_population;
        const income = data.census.median_household_income;
        const poverty = data.census.poverty_rate;
        
        html += `<div class="stat-box"><div class="number">${typeof pop === 'number' ? pop.toLocaleString() : pop}</div><div class="label">Population</div></div>`;
        html += `<div class="stat-box"><div class="number">$${typeof income === 'number' ? income.toLocaleString() : income}</div><div class="label">Median Income</div></div>`;
        html += `<div class="stat-box"><div class="number">${poverty}%</div><div class="label">Poverty Rate</div></div>`;
    }
    html += '</div>';
    
    // Top issues preview
    if (data.top_issues && data.top_issues.length > 0) {
        html += '<div class="card">';
        html += '<h2>Top Issues</h2>';
        data.top_issues.slice(0, 3).forEach(issue => {
            html += '<div class="issue-card">';
            html += `<h4>${issue.issue_name}</h4>`;
            html += `<p>${issue.significance}</p>`;
            html += `<div class="meta">${issue.story_count} stories | ${issue.date_range}</div>`;
            html += '</div>';
        });
        html += '</div>';
    }
    
    html += '</div>';
    return html;
}

// Render government tab
function renderGovernmentTab(county, data) {
    let html = '<div class="tab-content" id="government">';
    html += '<div class="card">';
    html += '<h2>County Officials</h2>';
    
    if (data.officials && data.officials.legislative_branch) {
        html += '<h3>Commissioners</h3>';
        html += '<table><thead><tr><th>Name</th><th>Title</th><th>Party</th></tr></thead><tbody>';
        data.officials.legislative_branch.forEach(official => {
            html += `<tr><td>${official.name}</td><td>${official.title || ''}</td><td>${official.party || ''}</td></tr>`;
        });
        html += '</tbody></table>';
    }
    
    if (data.officials && data.officials.other_info) {
        const info = data.officials.other_info;
        html += '<h3 class="mt-3">Contact & Meeting Information</h3>';
        html += '<table><tbody>';
        if (info.meeting_schedule) html += `<tr><td><strong>Meeting Schedule</strong></td><td>${info.meeting_schedule}</td></tr>`;
        if (info.address) html += `<tr><td><strong>Address</strong></td><td>${info.address}</td></tr>`;
        if (info.phone) html += `<tr><td><strong>Phone</strong></td><td>${info.phone}</td></tr>`;
        if (info.website) html += `<tr><td><strong>Website</strong></td><td><a href="${info.website}" target="_blank">${info.website}</a></td></tr>`;
        html += '</tbody></table>';
    }
    
    html += '</div>';
    html += '</div>';
    return html;
}

// Render issues tab
function renderIssuesTab(county, data, countyName) {
    let html = '<div class="tab-content" id="issues">';
    
    if (data.top_issues && data.top_issues.length > 0) {
        data.top_issues.forEach(issue => {
            html += '<div class="card">';
            html += `<h2>${issue.issue_name}</h2>`;
            html += `<div class="mb-2"><span class="tag">${issue.story_count} stories</span><span class="tag">${issue.date_range}</span></div>`;
            html += `<p><strong>Why it matters:</strong> ${issue.significance}</p>`;
            html += `<p><strong>Recent developments:</strong> ${issue.recent_developments}</p>`;
            html += '</div>';
        });
    } else {
        html += '<div class="card"><p class="text-muted">No issue data available.</p></div>';
    }
    
    html += '</div>';
    return html;
}

// Render budget tab
function renderBudgetTab(county, data) {
    let html = '<div class="tab-content" id="budget">';
    html += '<div class="card">';
    html += '<h2>Budget Overview</h2>';
    
    if (data.budget_summary) {
        html += `<div class="text-muted mb-3">${data.budget_summary}</div>`;
    } else {
        html += '<p class="text-muted">Detailed budget analysis available in source files.</p>';
    }
    
    html += '</div>';
    html += '</div>';
    return html;
}

// Render schools tab
function renderSchoolsTab(county, data) {
    let html = '<div class="tab-content" id="schools">';
    html += '<div class="card">';
    html += '<h2>Schools & Education</h2>';
    
    if (data.schools) {
        if (data.schools.superintendent) {
            html += `<p><strong>Superintendent:</strong> ${data.schools.superintendent}</p>`;
        }
        if (data.schools.board_members && data.schools.board_members.length > 0) {
            html += '<h3 class="mt-2">Board Members</h3><ul>';
            data.schools.board_members.forEach(member => {
                html += `<li>${member}</li>`;
            });
            html += '</ul>';
        }
        if (data.schools.schools) {
            html += `<p class="mt-2"><strong>Total Schools:</strong> ${data.schools.schools.length}</p>`;
        }
    } else {
        html += '<p class="text-muted">School data not available.</p>';
    }
    
    html += '</div>';
    html += '</div>';
    return html;
}

// Render stories tab
function renderStoriesTab(county, countyName) {
    let html = '<div class="tab-content" id="stories">';
    
    // Filter stories for this county
    const countyStories = storiesData.filter(story => 
        story.counties && story.counties.includes(countyName)
    );
    
    html += '<div class="card">';
    html += '<h2>Recent News Stories</h2>';
    html += `<p class="text-muted mb-3">${countyStories.length} stories found</p>`;
    
    // Search box
    html += '<div class="search-box">';
    html += '<input type="text" id="storySearch" placeholder="Search stories..." onkeyup="filterStories()">';
    html += '</div>';
    
    // Stories list
    html += '<div id="storiesList">';
    countyStories.slice(0, 20).forEach(story => {
        html += '<div class="story-item">';
        html += `<h4>${story.title}</h4>`;
        html += `<div class="date">${story.date} | ${story.author || 'Unknown author'}</div>`;
        if (story.beatbook_tag) {
            html += `<div class="mt-1"><span class="tag">${story.beatbook_tag}</span></div>`;
        }
        html += '</div>';
    });
    html += '</div>';
    
    html += '</div>';
    html += '</div>';
    return html;
}

// Show tab
function showTab(tabName) {
    // Hide all tabs
    document.querySelectorAll('.tab-content').forEach(tab => {
        tab.classList.remove('active');
    });
    document.querySelectorAll('.tab').forEach(tab => {
        tab.classList.remove('active');
    });
    
    // Show selected tab
    document.getElementById(tabName).classList.add('active');
    event.target.classList.add('active');
}

// Filter stories
function filterStories() {
    const searchTerm = document.getElementById('storySearch').value.toLowerCase();
    const countyName = {
        'caroline': 'Caroline County',
        'dorchester': 'Dorchester County',
        'kent': 'Kent County',
        'queen_annes': "Queen Anne's County",
        'talbot': 'Talbot County'
    }[currentCounty];
    
    const countyStories = storiesData.filter(story => 
        story.counties && story.counties.includes(countyName)
    );
    
    const filtered = countyStories.filter(story =>
        story.title.toLowerCase().includes(searchTerm) ||
        (story.author && story.author.toLowerCase().includes(searchTerm)) ||
        (story.beatbook_tag && story.beatbook_tag.toLowerCase().includes(searchTerm))
    );
    
    let html = '';
    filtered.slice(0, 20).forEach(story => {
        html += '<div class="story-item">';
        html += `<h4>${story.title}</h4>`;
        html += `<div class="date">${story.date} | ${story.author || 'Unknown author'}</div>`;
        if (story.beatbook_tag) {
            html += `<div class="mt-1"><span class="tag">${story.beatbook_tag}</span></div>`;
        }
        html += '</div>';
    });
    
    if (filtered.length === 0) {
        html = '<p class="text-muted text-center">No stories found matching your search.</p>';
    }
    
    document.getElementById('storiesList').innerHTML = html;
}
"""
    
    with open(OUTPUT_DIR / "js" / "app.js", 'w') as f:
        f.write(js_content)


def generate_index_html():
    """Generate the main HTML file."""
    html_content = """<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Five-County Beatbook | Maryland Eastern Shore</title>
    <link rel="stylesheet" href="css/style.css">
</head>
<body>
    <header>
        <div class="container">
            <h1>📰 Five-County Local Government Beatbook</h1>
            <p>Caroline, Dorchester, Kent, Queen Anne's, and Talbot Counties | Maryland Eastern Shore</p>
        </div>
    </header>
    
    <nav>
        <div class="container">
            <ul>
                <li><a href="#" data-page="overview" class="active">Overview</a></li>
                <li><a href="#" data-page="county" data-county="caroline">Caroline</a></li>
                <li><a href="#" data-page="county" data-county="dorchester">Dorchester</a></li>
                <li><a href="#" data-page="county" data-county="kent">Kent</a></li>
                <li><a href="#" data-page="county" data-county="queen_annes">Queen Anne's</a></li>
                <li><a href="#" data-page="county" data-county="talbot">Talbot</a></li>
            </ul>
        </div>
    </nav>
    
    <main id="content">
        <div class="container">
            <div class="loading">
                <h2>Loading data...</h2>
                <p>Please wait while we load county information.</p>
            </div>
        </div>
    </main>
    
    <footer>
        <div class="container">
            <p>Generated: November 30, 2025 | Data sources: County governments, MSDE, U.S. Census Bureau, local news archives</p>
        </div>
    </footer>
    
    <script src="js/app.js"></script>
</body>
</html>
"""
    
    with open(OUTPUT_DIR / "index.html", 'w') as f:
        f.write(html_content)


def prepare_data_files():
    """Prepare JSON data files for the website."""
    print("Preparing data files...")
    
    # Load stories
    stories_file = DATA_DIR / "beatbook_standardized_stories.json"
    stories_data = load_json_file(stories_file)
    
    # Save stories
    with open(OUTPUT_DIR / "data" / "stories.json", 'w') as f:
        json.dump(stories_data, f, indent=2)
    
    # Load and save data for each county
    for county in COUNTIES:
        county_dir = DATA_DIR / county
        county_data = {}
        
        # Census
        census_file = county_dir / f"{county}_census.json"
        county_data['census'] = load_json_file(census_file)
        
        # Officials
        officials_file = county_dir / f"{county}_county_officials.json"
        county_data['officials'] = load_json_file(officials_file)
        
        # Municipal officials
        muni_officials_file = county_dir / f"{county}_municipal_officials.json"
        county_data['municipal_officials'] = load_json_file(muni_officials_file)
        
        # Schools
        schools_file = county_dir / f"{county}_schools.json"
        county_data['schools'] = load_json_file(schools_file)
        
        # Elections
        elections_file = county_dir / f"{county}_elections.json"
        county_data['elections'] = load_json_file(elections_file)
        
        # Top issues
        top_issues_file = DATA_DIR / "top_issues_by_county.json"
        all_issues = load_json_file(top_issues_file)
        county_name = COUNTY_NAMES[county]
        county_data['top_issues'] = all_issues.get(county_name, [])
        
        # Budget summary (first part of budget analysis)
        budget_file = county_dir / f"{county}_budget_analysis.md"
        budget_content = load_file_content(budget_file)
        if budget_content:
            # Extract first 500 chars as summary
            county_data['budget_summary'] = budget_content[:500] + "..."
        
        # Save county data
        with open(OUTPUT_DIR / "data" / f"{county}_data.json", 'w') as f:
            json.dump(county_data, f, indent=2)
        
        print(f"  ✓ {COUNTY_NAMES[county]}")


def generate_website():
    """Main function to generate the website."""
    print("\n" + "="*80)
    print("FIVE-COUNTY BEATBOOK WEBSITE GENERATOR")
    print("="*80 + "\n")
    
    print("Step 1: Creating directory structure...")
    create_directory_structure()
    print("  ✓ Directories created\n")
    
    print("Step 2: Generating CSS...")
    generate_main_css()
    print("  ✓ CSS file created\n")
    
    print("Step 3: Generating JavaScript...")
    generate_main_js()
    print("  ✓ JavaScript file created\n")
    
    print("Step 4: Generating HTML...")
    generate_index_html()
    print("  ✓ HTML file created\n")
    
    print("Step 5: Preparing data files...")
    prepare_data_files()
    print("  ✓ Data files created\n")
    
    print("="*80)
    print("✓ WEBSITE GENERATED SUCCESSFULLY!")
    print("="*80)
    print(f"\nWebsite location: {OUTPUT_DIR}")
    print(f"\nTo view the website:")
    print(f"  1. Open: {OUTPUT_DIR / 'index.html'}")
    print(f"  2. Or run: python -m http.server 8000")
    print(f"     Then visit: http://localhost:8000/website/\n")
    
    return 0


if __name__ == "__main__":
    import sys
    sys.exit(generate_website())
