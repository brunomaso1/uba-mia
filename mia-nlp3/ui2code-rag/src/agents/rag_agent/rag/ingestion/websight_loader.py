import json, requests, os
from pathlib import Path
from typing import Any
from datetime import datetime
from loguru import logger

# Local dependencies
from src.config import (
    websight_data_dir,
    ui_examples_dir,
    websight_data_file_name,
    websight_download_steps,
    websight_download_offset,
    websight_download_length,
)
from ..core.documents import Document


class WebSightLoader:
    """
    Loader for WebSight dataset - converts UI screenshots to HTML/CSS examples
    """

    def __init__(self):
        """Initialize WebSight loader"""
        logger.info("Initializing WebSightLoader...")
        self.websight_dir = websight_data_dir()
        self.websight_data_file = websight_data_file_name
        self.examples_dir = ui_examples_dir()

        # Ensure directories exist
        self.websight_dir.mkdir(parents=True, exist_ok=True)
        self.examples_dir.mkdir(parents=True, exist_ok=True)
        logger.info(f"WebSight data dir: {self.websight_dir}")
        logger.info(f"UI examples dir: {self.examples_dir}")

    def load_websight_subset(self, max_examples: int = 1000) -> list[dict[str, Any]]:
        logger.info(f"Loading WebSight subset (max {max_examples})...")
        try:
            # Load from actual JSON files instead of cache/samples
            logger.info("Loading WebSight data from JSON files...")
            html_templates = self._get_sample_html_templates()

            if not html_templates:
                logger.warning("No HTML templates found in JSON files, using fallback samples")
                sample_data = self._create_sample_websight_data(min(max_examples, 20))
                return sample_data

            logger.info(f"Loaded {len(html_templates)} HTML templates from JSON files")

            # Convert to WebSight format (must match expected structure in websight_to_documents)
            websight_data = []
            for i, template in enumerate(html_templates[:max_examples]):
                websight_data.append(
                    {
                        "id": f"websight_{i:06d}",
                        "html": template.get("html", ""),
                        "url": f"websight://sample/{i}",
                        "metadata": {
                            "type": template.get("type", "unknown"),
                            "description": template.get("description", "No description"),
                            "components": template.get("components", []),
                            "created_at": "2025-01-01",
                        },
                    }
                )

            logger.info(f"Prepared {len(websight_data)} WebSight documents")
            return websight_data

        except Exception as e:
            logger.error(f"Error loading WebSight data: {e}", exc_info=True)
            return []

    def _get_fixed_sample_html(self) -> str:

        sample_templates = [
            {
                "type": "landing_page",
                "description": "Modern landing page with hero section, navigation, and call-to-action",
                "components": ["header", "nav", "hero", "cta", "footer"],
                "html": """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Product Landing</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-white">
            <header class="bg-white shadow-sm">
                <nav class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8 h-16 flex items-center justify-between">
                    <div class="text-2xl font-bold text-blue-600">ProductName</div>
                    <div class="hidden md:flex space-x-8">
                        <a href="#" class="text-gray-700 hover:text-blue-600">Features</a>
                        <a href="#" class="text-gray-700 hover:text-blue-600">Pricing</a>
                        <a href="#" class="text-gray-700 hover:text-blue-600">About</a>
                    </div>
                    <button class="bg-blue-600 text-white px-6 py-2 rounded-lg hover:bg-blue-700">Sign Up</button>
                </nav>
            </header>
            <main>
                <section class="py-20 text-center">
                    <div class="max-w-4xl mx-auto px-4">
                        <h1 class="text-5xl font-bold text-gray-900 mb-6">
                            Build Something Amazing
                        </h1>
                        <p class="text-xl text-gray-600 mb-8 max-w-2xl mx-auto">
                            Our platform helps you create, manage, and scale your ideas with powerful tools and intuitive design.
                        </p>
                        <div class="flex gap-4 justify-center">
                            <button class="bg-blue-600 text-white px-8 py-3 rounded-lg text-lg hover:bg-blue-700">
                                Get Started Free
                            </button>
                            <button class="border-2 border-gray-300 text-gray-700 px-8 py-3 rounded-lg text-lg hover:border-gray-400">
                                Watch Demo
                            </button>
                        </div>
                    </div>
                </section>
            </main>
        </body>
        </html>""",
            },
            {
                "type": "contact_form",
                "description": "Contact form with validation and modern styling",
                "components": ["form", "input", "textarea", "button", "validation"],
                "html": """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Contact Form</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50 py-12">
            <div class="max-w-md mx-auto bg-white rounded-xl shadow-md p-6">
                <h2 class="text-2xl font-bold text-gray-900 mb-6 text-center">Get In Touch</h2>
                <form class="space-y-4">
                    <div>
                        <label for="name" class="block text-sm font-medium text-gray-700 mb-1">Full Name</label>
                        <input type="text" id="name" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" required>
                    </div>
                    <div>
                        <label for="email" class="block text-sm font-medium text-gray-700 mb-1">Email Address</label>
                        <input type="email" id="email" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" required>
                    </div>
                    <div>
                        <label for="subject" class="block text-sm font-medium text-gray-700 mb-1">Subject</label>
                        <select id="subject" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500">
                            <option>General Inquiry</option>
                            <option>Support Request</option>
                            <option>Business Partnership</option>
                        </select>
                    </div>
                    <div>
                        <label for="message" class="block text-sm font-medium text-gray-700 mb-1">Message</label>
                        <textarea id="message" rows="4" class="w-full px-3 py-2 border border-gray-300 rounded-lg focus:ring-2 focus:ring-blue-500 focus:border-blue-500" required></textarea>
                    </div>
                    <button type="submit" class="w-full bg-blue-600 text-white py-3 rounded-lg hover:bg-blue-700 font-medium">
                        Send Message
                    </button>
                </form>
            </div>
        </body>
        </html>""",
            },
            {
                "type": "dashboard",
                "description": "Admin dashboard with sidebar, stats cards, and data tables",
                "components": ["sidebar", "nav", "cards", "table", "metrics"],
                "html": """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Admin Dashboard</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-100">
            <div class="flex h-screen">
                <aside class="w-64 bg-gray-800 text-white">
                    <div class="p-4">
                        <h1 class="text-xl font-bold">Admin Panel</h1>
                    </div>
                    <nav class="mt-4">
                        <a href="#" class="block px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">Dashboard</a>
                        <a href="#" class="block px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">Users</a>
                        <a href="#" class="block px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">Analytics</a>
                        <a href="#" class="block px-4 py-2 text-gray-300 hover:bg-gray-700 hover:text-white">Settings</a>
                    </nav>
                </aside>
                <main class="flex-1 p-6">
                    <h2 class="text-2xl font-bold text-gray-900 mb-6">Dashboard Overview</h2>
                    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-6 mb-8">
                        <div class="bg-white rounded-lg shadow p-6">
                            <div class="text-sm font-medium text-gray-500 mb-1">Total Users</div>
                            <div class="text-3xl font-bold text-gray-900">12,543</div>
                            <div class="text-sm text-green-600 mt-2">+2.5% from last month</div>
                        </div>
                        <div class="bg-white rounded-lg shadow p-6">
                            <div class="text-sm font-medium text-gray-500 mb-1">Revenue</div>
                            <div class="text-3xl font-bold text-gray-900">$47,832</div>
                            <div class="text-sm text-green-600 mt-2">+12.3% from last month</div>
                        </div>
                        <div class="bg-white rounded-lg shadow p-6">
                            <div class="text-sm font-medium text-gray-500 mb-1">Orders</div>
                            <div class="text-3xl font-bold text-gray-900">1,234</div>
                            <div class="text-sm text-red-600 mt-2">-3.1% from last month</div>
                        </div>
                        <div class="bg-white rounded-lg shadow p-6">
                            <div class="text-sm font-medium text-gray-500 mb-1">Conversion</div>
                            <div class="text-3xl font-bold text-gray-900">3.24%</div>
                            <div class="text-sm text-green-600 mt-2">+0.8% from last month</div>
                        </div>
                    </div>
                    <div class="bg-white rounded-lg shadow">
                        <div class="px-6 py-4 border-b border-gray-200">
                            <h3 class="text-lg font-medium text-gray-900">Recent Activity</h3>
                        </div>
                        <div class="overflow-x-auto">
                            <table class="min-w-full divide-y divide-gray-200">
                                <thead class="bg-gray-50">
                                    <tr>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">User</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Action</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Status</th>
                                        <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">Date</th>
                                    </tr>
                                </thead>
                                <tbody class="bg-white divide-y divide-gray-200">
                                    <tr>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-900">John Doe</td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">Created account</td>
                                        <td class="px-6 py-4 whitespace-nowrap">
                                            <span class="px-2 inline-flex text-xs leading-5 font-semibold rounded-full bg-green-100 text-green-800">Active</span>
                                        </td>
                                        <td class="px-6 py-4 whitespace-nowrap text-sm text-gray-500">2 hours ago</td>
                                    </tr>
                                </tbody>
                            </table>
                        </div>
                    </div>
                </main>
            </div>
        </body>
        </html>""",
            },
            {
                "type": "ecommerce_card",
                "description": "Product card for e-commerce with image, price, and actions",
                "components": ["card", "image", "price", "button", "rating"],
                "html": """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Product Card</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-gray-50 p-8">
            <div class="max-w-sm mx-auto bg-white rounded-xl shadow-lg overflow-hidden">
                <div class="relative">
                    <div class="h-48 bg-gradient-to-br from-blue-100 to-purple-100 flex items-center justify-center">
                        <div class="text-4xl font-bold text-gray-400">Product Image</div>
                    </div>
                    <div class="absolute top-4 right-4">
                        <span class="bg-red-500 text-white px-2 py-1 rounded-full text-sm font-medium">Sale</span>
                    </div>
                </div>
                <div class="p-6">
                    <div class="flex items-center mb-2">
                        <div class="flex text-yellow-400">
                            <span>★</span>
                            <span>★</span>
                            <span>★</span>
                            <span>★</span>
                            <span class="text-gray-300">★</span>
                        </div>
                        <span class="ml-2 text-sm text-gray-600">(124 reviews)</span>
                    </div>
                    <h3 class="text-lg font-semibold text-gray-900 mb-2">Premium Product Name</h3>
                    <p class="text-gray-600 text-sm mb-4">High-quality product with amazing features and excellent craftsmanship.</p>
                    <div class="flex items-center justify-between">
                        <div class="flex items-center space-x-2">
                            <span class="text-2xl font-bold text-gray-900">$89.99</span>
                            <span class="text-sm text-gray-500 line-through">$119.99</span>
                        </div>
                        <button class="bg-blue-600 text-white px-4 py-2 rounded-lg hover:bg-blue-700 font-medium">
                            Add to Cart
                        </button>
                    </div>
                </div>
            </div>
        </body>
        </html>""",
            },
            {
                "type": "blog_post",
                "description": "Blog post layout with header, content, and sidebar",
                "components": ["article", "header", "sidebar", "typography", "navigation"],
                "html": """<!DOCTYPE html>
        <html lang="en">
        <head>
            <meta charset="UTF-8">
            <meta name="viewport" content="width=device-width, initial-scale=1.0">
            <title>Blog Post</title>
            <script src="https://cdn.tailwindcss.com"></script>
        </head>
        <body class="bg-white">
            <div class="max-w-6xl mx-auto px-4 py-8">
                <div class="grid grid-cols-1 lg:grid-cols-3 gap-8">
                    <article class="lg:col-span-2">
                        <header class="mb-8">
                            <div class="text-sm text-blue-600 font-medium mb-2">Technology</div>
                            <h1 class="text-4xl font-bold text-gray-900 mb-4">
                                The Future of Web Development: Trends to Watch
                            </h1>
                            <div class="flex items-center text-gray-600 text-sm">
                                <span>By Alex Johnson</span>
                                <span class="mx-2">•</span>
                                <span>March 15, 2024</span>
                                <span class="mx-2">•</span>
                                <span>5 min read</span>
                            </div>
                        </header>
                        <div class="prose max-w-none">
                            <p class="text-lg text-gray-700 mb-6">
                                Web development continues to evolve at a rapid pace, with new technologies and frameworks emerging regularly. 
                                Understanding these trends is crucial for developers who want to stay competitive in the field.
                            </p>
                            <h2 class="text-2xl font-bold text-gray-900 mb-4 mt-8">Key Trends in 2024</h2>
                            <p class="text-gray-700 mb-4">
                                This year has brought significant changes to how we approach web development. From improved performance 
                                optimizations to better developer experience, the landscape is shifting.
                            </p>
                            <h3 class="text-xl font-semibold text-gray-900 mb-3 mt-6">1. Progressive Web Applications</h3>
                            <p class="text-gray-700 mb-4">
                                PWAs continue to bridge the gap between web and native applications, offering offline functionality 
                                and app-like experiences directly in the browser.
                            </p>
                            <h3 class="text-xl font-semibold text-gray-900 mb-3 mt-6">2. Serverless Architecture</h3>
                            <p class="text-gray-700 mb-4">
                                Serverless computing is becoming more mainstream, allowing developers to focus on code rather 
                                than infrastructure management.
                            </p>
                        </div>
                    </article>
                    <aside class="lg:col-span-1">
                        <div class="bg-gray-50 rounded-lg p-6 mb-6">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">About the Author</h3>
                            <div class="flex items-center mb-3">
                                <div class="w-12 h-12 bg-blue-500 rounded-full flex items-center justify-center text-white font-bold">
                                    AJ
                                </div>
                                <div class="ml-3">
                                    <div class="font-medium text-gray-900">Alex Johnson</div>
                                    <div class="text-sm text-gray-600">Senior Developer</div>
                                </div>
                            </div>
                            <p class="text-sm text-gray-600">
                                Full-stack developer with 8+ years of experience in modern web technologies.
                            </p>
                        </div>
                        <div class="bg-gray-50 rounded-lg p-6">
                            <h3 class="text-lg font-semibold text-gray-900 mb-4">Related Posts</h3>
                            <div class="space-y-3">
                                <a href="#" class="block text-sm text-gray-700 hover:text-blue-600">
                                    Getting Started with React Hooks
                                </a>
                                <a href="#" class="block text-sm text-gray-700 hover:text-blue-600">
                                    CSS Grid vs Flexbox: When to Use Each
                                </a>
                                <a href="#" class="block text-sm text-gray-700 hover:text-blue-600">
                                    Modern JavaScript Best Practices
                                </a>
                            </div>
                        </div>
                    </aside>
                </div>
            </div>
        </body>
        </html>""",
            },
        ]

        return sample_templates

    def _get_sample_html_templates(self) -> list[str]:
        logger.info("Getting sample HTML templates from files...")
        html_samples = []
        # Recorrer los archivos JSON con el prefijo en el directorio websight_dir

        logger.info(f"Looking for files with prefix: {self.websight_data_file} in {self.websight_dir}")

        for file in self.websight_dir.glob(f"{self.websight_data_file}*.json"):
            logger.info(f"Reading file: {file}")
            try:
                with open(file, "r", encoding="utf-8") as f:
                    data = json.load(f)
                rows = data.get("rows", [])
                for item in rows:
                    row = item.get("row", {})
                    html_text = row.get("text", "")
                    description = row.get("llm_generated_idea", "")
                    if html_text:
                        html = {
                            "type": "ecommerce_card",
                            "description": description,
                            "components": ["card", "image", "price", "button", "rating"],
                            "html": html_text,
                        }
                        html_samples.append(html)

                logger.info(f"Extracted {len(rows)} rows from {file}")
            except Exception as e:
                logger.error(f"Error leyendo {file}: {e}", exc_info=True)
        logger.info(f"Total HTML samples found: {len(html_samples)}")
        return html_samples

    def _create_sample_websight_data(self, num_samples: int) -> list[dict[str, Any]]:
        logger.info(f"Creating {num_samples} sample WebSight data entries...")
        sample_templates = self._get_sample_html_templates()

        if not sample_templates:
            logger.info("No sample templates found in files, using fixed samples.")
            sample_templates = self._get_fixed_sample_html()
        samples = []

        for i in range(min(num_samples, len(sample_templates) * 5)):
            template_idx = i % len(sample_templates)
            template = sample_templates[template_idx]
            sample = {
                "id": f"websight_sample_{i:04d}",
                "url": f"https://example-{i}.com",
                "html": template["html"],
                "text": self._extract_text_from_html(template["html"]),
                "metadata": {
                    "type": "unknown",
                    "description": template["description"],
                    "components": [],
                    "created_at": datetime.now().isoformat(),
                    "source": "websight_dataset",
                },
            }
            samples.append(sample)
        logger.info(f"Created {len(samples)} sample entries.")
        return samples

    def _extract_text_from_html(self, html: str) -> str:
        logger.debug("Extracting text from HTML...")
        try:
            from bs4 import BeautifulSoup

            soup = BeautifulSoup(html, "html.parser")
            return soup.get_text(separator=" ", strip=True)
        except ImportError:
            logger.warning("BeautifulSoup not installed, using regex fallback.")
            import re

            text = re.sub(r"<[^>]+>", " ", html)
            text = re.sub(r"\s+", " ", text)
            return text.strip()

    def websight_to_documents(self, websight_data: list[dict[str, Any]]) -> list[Document]:
        logger.info(f"Converting {len(websight_data)} WebSight entries to Document objects...")
        documents = []
        for entry in websight_data:
            try:
                search_text = self._create_search_text(entry)
                metadata_text = f"Type: {entry['metadata']['type']} | Description: {entry['metadata']['description']} | Components: {', '.join(entry['metadata']['components'])}"
                full_text = f"{metadata_text} | {search_text}"
                doc = Document(id=entry["id"], text=full_text, source=f"websight:{entry['id']}")
                doc.websight_id = entry["id"]
                doc.url = entry.get("url", "unknown")
                doc.html_code = entry["html"]
                doc.doc_type = entry["metadata"]["type"]
                doc.description = entry["metadata"]["description"]
                doc.components = entry["metadata"]["components"]
                doc.created_at = entry["metadata"].get("created_at")
                doc.source_type = "websight"
                doc.filename = f"{entry['id']}.html"
                documents.append(doc)
            except Exception as e:
                logger.error(f"Error converting WebSight entry {entry.get('id', 'unknown')}: {e}", exc_info=True)
                continue
        logger.info(f"Converted {len(documents)} documents.")
        return documents

    def _create_search_text(self, entry: dict[str, Any]) -> str:
        """Create searchable text from WebSight entry"""
        parts = []

        # Add metadata description
        if "metadata" in entry and "description" in entry["metadata"]:
            parts.append(f"Description: {entry['metadata']['description']}")

        # Add components
        if "metadata" in entry and "components" in entry["metadata"]:
            components = entry["metadata"]["components"]
            parts.append(f"UI Components: {', '.join(components)}")

        # Add type
        if "metadata" in entry and "type" in entry["metadata"]:
            parts.append(f"Type: {entry['metadata']['type']}")

        # Add extracted text from HTML
        if "text" in entry:
            parts.append(f"Content: {entry['text'][:500]}...")  # Limit content length

        # Add HTML structure information
        html = entry.get("html", "")
        html_keywords = self._extract_html_keywords(html)
        if html_keywords:
            parts.append(f"HTML Elements: {', '.join(html_keywords)}")

        return " | ".join(parts)

    def _extract_html_keywords(self, html: str) -> list[str]:
        """Extract important HTML elements and classes for search"""
        import re

        keywords = set()

        # Extract HTML tags
        tags = re.findall(r"<(\w+)", html)
        keywords.update(tags)

        # Extract class names
        classes = re.findall(r'class="([^"]*)"', html)
        for class_list in classes:
            class_names = class_list.split()
            # Add only meaningful Tailwind classes
            meaningful_classes = [
                c
                for c in class_names
                if any(
                    prefix in c
                    for prefix in ["bg-", "text-", "p-", "m-", "w-", "h-", "flex", "grid", "rounded", "shadow"]
                )
            ]
            keywords.update(meaningful_classes[:5])  # Limit to 5 most relevant classes

        return list(keywords)

    def save_html_examples(self, documents: list[Document]) -> int:
        logger.info(f"Saving {len(documents)} HTML examples to {self.examples_dir}...")
        saved_count = 0
        for doc in documents:
            try:
                # Get filename from document attributes
                filename = getattr(doc, "filename", f"{doc.id}.html")
                if not filename.endswith(".html"):
                    filename += ".html"

                # Save HTML file
                file_path = self.examples_dir / filename

                html_code = getattr(doc, "html_code", "")
                if html_code:
                    with open(file_path, "w", encoding="utf-8") as f:
                        f.write(html_code)
                    saved_count += 1

                    # Save metadata
                    metadata_path = file_path.with_suffix(".json")
                    metadata = {
                        "websight_id": getattr(doc, "websight_id", doc.id),
                        "url": getattr(doc, "url", "unknown"),
                        "type": getattr(doc, "doc_type", "unknown"),
                        "description": getattr(doc, "description", ""),
                        "components": getattr(doc, "components", []),
                        "created_at": getattr(doc, "created_at", ""),
                        "source_type": getattr(doc, "source_type", "websight"),
                        "search_text": doc.text,
                        "saved_at": datetime.now().isoformat(),
                    }
                    with open(metadata_path, "w", encoding="utf-8") as f:
                        json.dump(metadata, f, indent=2)
                    logger.debug(f"Saved HTML and metadata for {doc.id}")
            except Exception as e:
                logger.error(f"Error saving document {doc.id}: {e}", exc_info=True)
        logger.info(f"Saved {saved_count} HTML examples.")
        return saved_count

    def load_full_websight_pipeline(self, max_examples: int = 1000) -> list[Document]:
        logger.info(f"Starting full WebSight pipeline (max {max_examples})...")
        try:
            websight_data = self.load_websight_subset(max_examples)
            if not websight_data:
                logger.warning("No WebSight data available")
                return []
            logger.info(f"Converting {len(websight_data)} entries to Documents...")
            documents = self.websight_to_documents(websight_data)
            self.save_html_examples(documents)
            logger.info(f"WebSight pipeline complete: {len(documents)} documents ready")
            return documents
        except Exception as e:
            logger.error(f"Error in WebSight pipeline: {e}", exc_info=True)
            return []

    def download_websight_data(
        self,
        output_dir: Path = websight_data_dir,
        websight_steps: int = websight_download_steps,
        websight_offset: int = websight_download_offset,
        websight_length: int = websight_download_length,
    ):
        """
        Descarga el dataset WebSight en múltiples pasos usando la API de HuggingFace Datasets-Server.

        Args:
            output_dir (str): Directorio donde se guardarán los archivos JSON.
            websight_steps (int): Cantidad de filas a descargar por request.
            websight_offset (int): Offset inicial.
            websight_length (int): Límite superior del rango de offsets a descargar.
        """
        output_dir.mkdir(parents=True, exist_ok=True)
        for step in range(websight_offset, websight_length + 1, websight_steps):
            logger.debug(f"Descargando offset {step}...")
            url = (
                f"https://datasets-server.huggingface.co/rows?"
                f"dataset=HuggingFaceM4%2FWebSight&config=v0.2&split=train"
                f"&offset={step}&length={websight_steps}"
            )
            output_file = output_dir / f"websight_{step}.json"
            try:
                response = requests.get(url, timeout=60)
                response.raise_for_status()
                with open(output_file, "w", encoding="utf-8") as f:
                    f.write(response.text)
                logger.debug(f"Guardado en {output_file}")
            except requests.RequestException as e:
                logger.error(f"Error descargando offset {step}: {e}")