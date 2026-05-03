"""Screenshots package: extract embedded images + async Blob upload (per architecture.md §4.6).

- extractor.py: build ScreenshotRecord from ParserResult.embedded_images
- uploader.py: async ScreenshotUploader with SHA256 dedup against Azurite/Azure Blob
"""
