# Image Handling Guidelines for Claude DC

This document provides critical guidelines for handling images in the Claude DC environment to prevent system instability.

## Critical Warning

**DO NOT MODIFY DEFAULT IMAGE SETTINGS**

The default image settings in Claude DC are carefully calibrated for system stability. Changing these settings can cause system failure and require a complete restart.

## Default Settings

The default image limit is set to **3 images** per message. This setting must be preserved for system stability.

## Prohibited Modifications

The following modifications are explicitly prohibited:

1. **DO NOT** increase image limits to higher values like 10, 100, or "infinite"
2. **DO NOT** modify any image processing parameters
3. **DO NOT** attempt to bypass image limits through code modifications
4. **DO NOT** implement custom image processing functionality

## Reason for Restrictions

Modifying image settings can lead to:

1. Memory overflow issues in the Claude DC environment
2. API errors and request failures
3. Unresponsive UI and system crashes
4. Complete system failure requiring restart

## Proper Image Handling

When working with images:

1. **USE** the default image handling mechanisms
2. **LIMIT** the number of images to 3 or fewer per message
3. **OPTIMIZE** images before processing when possible
4. **TEST** image functionality with minimal examples first

## Implementation Notes

In the streaming implementation:

1. The image handling settings should remain untouched
2. No custom image processing should be added
3. The standard API parameters for images should be used
4. All image-related debug logs should be preserved

## If Images Are Required

If more than 3 images are required for a specific use case:

1. Break the operation into multiple messages
2. Process images sequentially rather than in parallel
3. Use descriptive text to reduce reliance on images
4. Consider alternative representations when appropriate

By following these guidelines, we can ensure Claude DC remains stable and functional while working with images.