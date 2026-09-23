# Security Specification & Test Matrix

## 1. Data Invariants
1. A project cannot be created without matching `userId == request.auth.uid`.
2. A project's `id` in the payload must strictly match the Firestore document ID `{projectId}`.
3. Users can only read, write, update, and delete their own projects (`resource.data.userId == request.auth.uid`).
4. User profile at `/users/{userId}` can only be read and written by the authenticated user whose `uid == userId`.
5. Global default catch-all rule denies all unauthorized access (`match /{document=**} { allow read, write: if false; }`).
6. All IDs must adhere to regex format `^[a-zA-Z0-9_\-]+$` and length <= 128.
7. Title and description must have strict bounded sizes (`title.size() <= 300`, `description.size() <= 2000`).

## 2. The Dirty Dozen Payloads (Rejection Matrix)
1. **Unauthenticated Project Creation**: Writing to `/projects/p1` with `request.auth == null` -> DENIED.
2. **Identity Spoofing on Project**: Writing `userId: "victim_user"` when `request.auth.uid == "attacker"` -> DENIED.
3. **Cross-Tenant Project Read**: Authenticated user B attempting `get` on `/projects/p1` owned by user A -> DENIED.
4. **Cross-Tenant Project List**: Authenticated user B running list query without `userId == request.auth.uid` filter -> DENIED.
5. **Cross-Tenant Project Modification**: Authenticated user B attempting `update` on user A's project -> DENIED.
6. **Cross-Tenant Project Deletion**: Authenticated user B attempting `delete` on user A's project -> DENIED.
7. **Document ID Mismatch**: Writing project where payload `id != "proj_999"` to `/projects/proj_999` -> DENIED.
8. **Malicious Giant ID Injection**: Writing to `/projects/` with path ID longer than 128 chars or non-alphanumeric -> DENIED.
9. **Denial-of-Wallet Giant Title**: Writing project with title exceeding 300 characters -> DENIED.
10. **Denial-of-Wallet Giant Description**: Writing project with description exceeding 2000 characters -> DENIED.
11. **User Profile Impersonation**: User A attempting to write `/users/userB` -> DENIED.
12. **Catch-All Default Deny**: Querying or writing to any random unmapped collection `/system_secrets/keys` -> DENIED.
