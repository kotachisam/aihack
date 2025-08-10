import warnings

# Suppress the specific NotOpenSSLWarning as early as possible by matching its message.
# This avoids importing urllib3, which might trigger the warning itself.
warnings.filterwarnings("ignore", message=".*urllib3 v2 only supports OpenSSL 1.1.1+.*")
