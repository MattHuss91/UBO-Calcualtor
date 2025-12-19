<!DOCTYPE html>
<html lang="en-GB">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    
</head>
<body>
<h1>UBO Calculator</h1>

<p>A web-based tool for calculating Ultimate Beneficial Ownership (UBO) in multi-layered business structures.</p>

<h2>Overview</h2>

<p>The UBO Calculator helps staff and management identify ultimate beneficial owners across complex corporate structures. It automatically traces ownership through multiple layers of companies and calculates each person's or entity's ultimate ownership percentage in the target business.</p>

<h2>Key Features</h2>

<ul class="feature-list">
    <li><strong>Visual ownership diagrams</strong> - Clear graphical representation of ownership structures with colour-coded entities (blue for companies, orange for people)</li>
    <li><strong>Automatic UBO calculation</strong> - Traces ownership paths through multiple layers and calculates ultimate ownership percentages</li>
    <li><strong>Dual relationship tracking</strong> - Records both equity ownership and directorship roles</li>
    <li><strong>Layer organisation</strong> - Arrange entities in visual layers for clear hierarchy display</li>
    <li><strong>Validation checks</strong> - Automatic validation that ownership percentages sum correctly</li>
    <li><strong>Data export</strong> - Download entities, relationships, ultimate ownership data and diagrams as CSV/PNG files</li>
    <li><strong>Quick setup tools</strong> - Helper function to create multiple equal-share directors in one step</li>
</ul>

<h2>Use Cases</h2>

<p>This tool is designed for:</p>
<ul>
    <li>Compliance teams verifying beneficial ownership for regulatory requirements</li>
    <li>Due diligence during mergers and acquisitions</li>
    <li>Legal teams mapping corporate structures</li>
    <li>Management reviewing ownership positions</li>
    <li>Anyone needing to understand complex multi-tier ownership structures</li>
</ul>

<h2>Benefits</h2>

<ul class="feature-list">
    <li><strong>Reduces human error</strong> - Automated calculations eliminate manual arithmetic mistakes</li>
    <li><strong>Improves efficiency</strong> - Complex ownership structures calculated instantly</li>
    <li><strong>Reduces completion time</strong> - Tasks that previously took hours now take minutes</li>
    <li><strong>Clear understanding</strong> - Visual diagrams make complex structures easy to comprehend</li>
    <li><strong>Audit trail</strong> - Export all data for documentation and compliance purposes</li>
</ul>

<h2>How It Works</h2>

<ol>
    <li><strong>Add entities</strong> - Create companies and people in your ownership structure</li>
    <li><strong>Define relationships</strong> - Set up equity ownership percentages and directorship roles</li>
    <li><strong>Set target company</strong> - Select which business you want to analyse</li>
    <li><strong>View results</strong> - See ultimate ownership percentages and visual diagram automatically</li>
</ol>

<h3>Example</h3>

<div class="example-box">
    <p>If Matt Ltd is owned 50% by yourself and 50% by Matt Holdings, and Matt Holdings is owned 25% by Claude and 75% by Mike, the calculator will show:</p>
    <ul>
        <li>You: 50% of Matt Ltd</li>
        <li>Claude: 12.5% of Matt Ltd (25% × 50%)</li>
        <li>Mike: 37.5% of Matt Ltd (75% × 50%)</li>
    </ul>
</div>

<h2>Getting Started</h2>

<h3>Running Locally</h3>

<ol>
    <li>Install Python dependencies:
<pre><code>pip install -r requirements.txt</code></pre>
    </li>
    <li>Run the application:
<pre><code>streamlit run app.py</code></pre>
    </li>
    <li>Open your browser to <code>http://localhost:8501</code></li>
</ol>

<h3>Deploying to Streamlit Cloud</h3>

<ol>
    <li>Push your code to GitHub</li>
    <li>Connect your repository to Streamlit Cloud</li>
    <li>Deploy with the following files:
        <ul>
            <li><code>app.py</code> - Main application</li>
            <li><code>requirements.txt</code> - Python dependencies</li>
            <li><code>packages.txt</code> - System dependencies</li>
        </ul>
    </li>
</ol>

<h2>Data Privacy</h2>

<ul class="feature-list">
    <li><strong>No persistent storage</strong> - All data exists only in your browser session</li>
    <li><strong>Session-based</strong> - Data resets when you close the browser tab or refresh</li>
    <li><strong>No data transmission</strong> - Information never leaves your machine except via manual downloads</li>
    <li><strong>Public data</strong> - Tool is designed for publicly available UBO information only</li>
</ul>

<p>This tool is safe for work use as it handles public beneficial ownership information that is typically available through Companies House or similar registries.</p>

<h2>Technical Details</h2>

<p>Built with:</p>
<div class="tech-stack">
    <span class="tech-badge">Streamlit</span>
    <span class="tech-badge">Python</span>
    <span class="tech-badge">Pandas</span>
    <span class="tech-badge">Graphviz</span>
</div>

<h3>Core Technologies</h3>
<ul>
    <li><strong>Streamlit</strong> - Web application framework</li>
    <li><strong>Pandas</strong> - Data manipulation and analysis</li>
    <li><strong>Graphviz</strong> - Diagram generation and visualisation</li>
</ul>

<h2>Requirements</h2>

<ul>
    <li>Python 3.7+</li>
    <li>See <code>requirements.txt</code> for full dependency list</li>
</ul>

<h2>Limitations</h2>

<ul>
    <li>UBO threshold is adjustable (default 25%) but must be set before analysis</li>
    <li>Circular ownership structures are not supported</li>
    <li>Maximum 10 visual layers for diagram clarity</li>
</ul>

</body>
</html>
