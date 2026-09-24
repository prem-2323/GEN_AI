"""MongoDB GridFS Service — manages binary storage for sources, images, and export artifacts.

Bucket: contentforge_files
Collections created by GridFS:
  - contentforge_files.files (metadata, size, filename, contentType, uploadDate, metadata dict)
  - contentforge_files.chunks (binary chunks up to 255KB each)
"""
from __future__ import annotations

import io
import logging
from typing import Any, BinaryIO, Dict, List, Optional, Tuple, Union
from bson import ObjectId
from fastapi import HTTPException
from gridfs import GridFSBucket
from pymongo.collection import Collection

from ..config.mongo import get_mongo_db

log = logging.getLogger("gen-transform.gridfs")

GRIDFS_BUCKET_NAME = "contentforge_files"


def get_gridfs_bucket() -> GridFSBucket:
    """Get the singleton GridFSBucket instance for contentforge_files."""
    db = get_mongo_db()
    return GridFSBucket(db, bucket_name=GRIDFS_BUCKET_NAME)


def get_gridfs_files_collection() -> Collection:
    """Access the metadata collection for contentforge_files."""
    db = get_mongo_db()
    return db[f"{GRIDFS_BUCKET_NAME}.files"]


def upload_gridfs_file(
    uid: str,
    project_id: str,
    filename: str,
    data: Union[bytes, BinaryIO],
    content_type: str = "application/octet-stream",
    file_type: str = "source",
    source_id: Optional[str] = None,
    deliverable_id: Optional[str] = None,
    extra_meta: Optional[Dict[str, Any]] = None,
) -> str:
    """Upload a binary file into GridFS with user ownership metadata.
    
    Returns the stringified ObjectId (fileId).
    """
    bucket = get_gridfs_bucket()
    
    metadata = {
        "firebaseUid": uid,
        "userId": uid,
        "projectId": project_id,
        "fileType": file_type,
        "originalFilename": filename,
        "contentType": content_type,
    }
    if source_id:
        metadata["sourceId"] = source_id
    if deliverable_id:
        metadata["deliverableId"] = deliverable_id
    if extra_meta:
        metadata.update(extra_meta)

    if isinstance(data, bytes):
        stream = io.BytesIO(data)
    else:
        stream = data

    file_id = bucket.upload_from_stream(
        filename=filename,
        source=stream,
        metadata=metadata,
    )
    file_id_str = str(file_id)
    log.info("Uploaded GridFS file: id=%s name=%s type=%s size_type=%s uid=%s", file_id_str, filename, file_type, type(data).__name__, uid)
    return file_id_str


def download_gridfs_file(file_id: str, uid: Optional[str] = None) -> Tuple[bytes, Dict[str, Any]]:
    """Download a file's raw bytes and metadata from GridFS with strict tenant ownership check.
    
    Raises 404 if not found, 403 if uid does not match metadata.firebaseUid.
    """
    try:
        oid = ObjectId(file_id)
    except Exception:
        raise HTTPException(status_code=400, detail="Invalid GridFS file ID format.")

    bucket = get_gridfs_bucket()
    files_col = get_gridfs_files_collection()
    
    file_doc = files_col.find_one({"_id": oid})
    if not file_doc:
        raise HTTPException(status_code=404, detail="File not found in GridFS.")

    meta = file_doc.get("metadata", {})
    if uid:
        owner_uid = meta.get("firebaseUid") or meta.get("userId")
        if owner_uid and owner_uid != uid:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this file.")

    out_stream = io.BytesIO()
    try:
        bucket.download_to_stream(oid, out_stream)
    except Exception as exc:
        log.error("Failed to download GridFS file %s: %s", file_id, exc)
        raise HTTPException(status_code=500, detail="Could not retrieve file binary from GridFS.")

    data_bytes = out_stream.getvalue()
    meta_info = {
        "fileId": file_id,
        "filename": file_doc.get("filename", "download.bin"),
        "contentType": meta.get("contentType") or "application/octet-stream",
        "length": file_doc.get("length", len(data_bytes)),
        "uploadDate": file_doc.get("uploadDate"),
        "metadata": meta,
    }
    return data_bytes, meta_info


def delete_gridfs_file(file_id: str, uid: Optional[str] = None) -> bool:
    """Delete a file from GridFS with tenant ownership check."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        return False

    bucket = get_gridfs_bucket()
    files_col = get_gridfs_files_collection()
    
    file_doc = files_col.find_one({"_id": oid})
    if not file_doc:
        return False

    meta = file_doc.get("metadata", {})
    if uid:
        owner_uid = meta.get("firebaseUid") or meta.get("userId")
        if owner_uid and owner_uid != uid:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this file.")

    try:
        bucket.delete(oid)
        log.info("Deleted GridFS file: id=%s uid=%s", file_id, uid)
        return True
    except Exception as exc:
        log.error("Failed to delete GridFS file %s: %s", file_id, exc)
        return False


def get_gridfs_file_doc(file_id: str, uid: Optional[str] = None) -> Optional[Dict[str, Any]]:
    """Retrieve metadata of a GridFS file without streaming bytes."""
    try:
        oid = ObjectId(file_id)
    except Exception:
        return None

    files_col = get_gridfs_files_collection()
    doc = files_col.find_one({"_id": oid})
    if not doc:
        return None

    meta = doc.get("metadata", {})
    if uid:
        owner_uid = meta.get("firebaseUid") or meta.get("userId")
        if owner_uid and owner_uid != uid:
            raise HTTPException(status_code=403, detail="Access denied. You do not own this file.")

    return {
        "fileId": str(doc["_id"]),
        "filename": doc.get("filename"),
        "length": doc.get("length"),
        "uploadDate": doc.get("uploadDate"),
        "contentType": meta.get("contentType"),
        "metadata": meta,
    }
