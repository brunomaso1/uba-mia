"""
Download WebSight dataset from HuggingFace and save to corpus directory
"""
import sys
from pathlib import Path
from datetime import datetime
import json

# Add src to path
sys.path.append(str(Path(__file__).parent.parent))

from src.config import corpus_dir

try:
    from datasets import load_dataset
except ImportError:
    print("Error: 'datasets' library not found.")
    print("Install with: pip install datasets")
    sys.exit(1)


def download_websight_to_corpus(num_samples: int = 1000, split: str = "train"):
    """
    Download WebSight dataset and save HTML files to corpus directory
    
    Args:
        num_samples: Number of samples to download
        split: Dataset split ('train' or 'test')
    """
    print("=" * 70)
    print(f"WebSight Dataset Downloader")
    print("=" * 70)
    print(f"\nDownloading {num_samples} samples from HuggingFace...")
    print(f"Dataset: HuggingFaceM4/WebSight")
    print(f"Split: {split}\n")
    
    # Create corpus subdirectory for WebSight
    websight_corpus = corpus_dir() / "websight"
    websight_corpus.mkdir(parents=True, exist_ok=True)
    
    print(f"Corpus directory: {websight_corpus}\n")
    
    # Load dataset
    try:
        dataset = load_dataset(
            "HuggingFaceM4/WebSight",
            split=f"{split}[:{num_samples}]",
            trust_remote_code=True
        )
        print(f"✓ Dataset loaded: {len(dataset)} samples\n")
    except Exception as e:
        print(f"✗ Error loading dataset: {e}")
        print("\nNote: WebSight is a large dataset and may take time to download.")
        return
    
    # Save each sample as HTML file
    saved_count = 0
    
    print("Saving HTML files to corpus...")
    for idx, item in enumerate(dataset):
        try:
            # Extract HTML code (WebSight stores it in 'text' field)
            html_code = item.get('text', '')
            
            if not html_code or len(html_code) < 50:
                continue
            
            # Create filename
            filename = f"websight_{idx:06d}.html"
            file_path = websight_corpus / filename
            
            # Save HTML file
            with open(file_path, 'w', encoding='utf-8') as f:
                f.write(html_code)
            
            # Extract and save metadata
            metadata = extract_metadata_from_html(html_code, idx)
            metadata_path = file_path.with_suffix('.json')
            
            with open(metadata_path, 'w', encoding='utf-8') as f:
                json.dump(metadata, f, indent=2)
            
            saved_count += 1
            
            # Progress indicator
            if (idx + 1) % 50 == 0:
                print(f"  Progress: {idx + 1}/{len(dataset)} files saved...")
                
        except Exception as e:
            print(f"  Warning: Failed to save sample {idx}: {e}")
            continue
    
    print(f"\n✓ Successfully saved {saved_count} HTML files")
    print(f"✓ Location: {websight_corpus}")
    print("\n" + "=" * 70)
    print("Download complete! Ready to process with RAG pipeline.")
    print("=" * 70)
    
    # Create index file
    create_corpus_index(websight_corpus, saved_count)


def extract_metadata_from_html(html: str, index: int) -> dict:
    """Extract metadata from HTML code"""
    import re
    
    metadata = {
        "id": f"websight_{index:06d}",
        "source": "HuggingFaceM4/WebSight",
        "downloaded_at": datetime.now().isoformat(),
        "components": [],
        "css_patterns": [],
        "frameworks": [],
        "length": len(html)
    }
    
    # Detect components
    components = set()
    component_tags = ['nav', 'header', 'footer', 'aside', 'section', 'article',
                      'form', 'button', 'input', 'table', 'card', 'modal']
    
    for tag in component_tags:
        if f'<{tag}' in html.lower():
            components.add(tag)
    
    metadata["components"] = list(components)
    
    # Detect CSS patterns
    if 'flexbox' in html.lower() or 'display: flex' in html.lower() or 'flex-' in html:
        metadata["css_patterns"].append('flexbox')
    if 'grid' in html.lower() or 'display: grid' in html.lower():
        metadata["css_patterns"].append('grid')
    if '@media' in html:
        metadata["css_patterns"].append('responsive')
    if 'animation' in html.lower() or '@keyframes' in html:
        metadata["css_patterns"].append('animations')
    if 'transition' in html.lower():
        metadata["css_patterns"].append('transitions')
    
    # Detect frameworks
    if 'tailwind' in html.lower() or any(c in html for c in ['bg-', 'text-', 'flex-', 'grid-']):
        metadata["frameworks"].append('tailwind')
    if 'bootstrap' in html.lower():
        metadata["frameworks"].append('bootstrap')
    
    return metadata


def create_corpus_index(corpus_path: Path, count: int):
    """Create index file with corpus information"""
    index_data = {
        "dataset": "WebSight",
        "source": "HuggingFaceM4/WebSight",
        "total_files": count,
        "created_at": datetime.now().isoformat(),
        "format": "HTML files with JSON metadata",
        "location": str(corpus_path)
    }
    
    index_path = corpus_path / "corpus_index.json"
    with open(index_path, 'w', encoding='utf-8') as f:
        json.dump(index_data, f, indent=2)
    
    print(f"✓ Created corpus index: {index_path}")


if __name__ == "__main__":
    import argparse
    
    parser = argparse.ArgumentParser(description='Download WebSight dataset to corpus')
    parser.add_argument('--samples', type=int, default=1000, help='Number of samples to download')
    parser.add_argument('--split', type=str, default='train', choices=['train', 'test'], help='Dataset split')
    
    args = parser.parse_args()
    
    download_websight_to_corpus(args.samples, args.split)