"""Credential-free local readiness; never claims account authentication."""
import argparse
from importlib.metadata import version, PackageNotFoundError
import sys


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['ready', 'disconnect'])
    args = parser.parse_args(argv)
    if args.action == 'disconnect':
        print('NO_EXTERNAL_CREDENTIALS_TO_REVOKE')
        return 0
    try:
        import wangbin_document_engine
        from .host_session import PROTOCOL_VERSION
        ready = (sys.version_info >= (3, 12) and sys.version_info < (3, 15)
                 and version('wangbin-document-cli') == '1.2.0'
                 and version('wangbin-solar-pv-input') == '0.3.1'
                 and PROTOCOL_VERSION == 'native-host-session/2.0')
    except (ImportError, PackageNotFoundError):
        ready = False
    print('LOCAL_READY' if ready else 'LOCAL_RUNTIME_UNAVAILABLE')
    return 0 if ready else 2


if __name__ == '__main__':
    raise SystemExit(main())
