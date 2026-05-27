import sys
import argparse
import json
from src.core.engine import GeocoderEngine
from src.exceptions import GeocoderError, AddressNotFoundError

def main():
    parser = argparse.ArgumentParser(
        description="Геокодер для российских адресов (JSON-вывод).",
        epilog="Коды возврата: 0 — Success, 1 — Handled Error, 2 — Critical Error."
    )
    parser.add_argument('-a', '--address', type=str, metavar="ADDR", help='Одиночный адрес в свободной формe')
    parser.add_argument('-i', '--input', type=str, help='Путь к входному файлу со списком адресов')
    parser.add_argument('-o', '--output', type=str, help='Путь к файлу для сохранения результатов')
    parser.add_argument('--debug', action='store_true',
                        help='Режим отладки (вывод Traceback)')

    args = parser.parse_args()

    if not args.address and not args.input:
        parser.print_help() #печатает description, epilog и все help флагов
        sys.exit(0)

    if args.input and not args.output:
        error_json = {
            "status": "error",
            "message": "При использовании пакетного режима (-i) необходимо указать выходной файл (-o)."
        }
        print(json.dumps(error_json, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)

    try:
        engine = GeocoderEngine()
        if args.address:
            #одиночный режим
            result = engine.geocode(args.address)
            print(json.dumps(result, ensure_ascii=False, indent=2))
        elif args.input:
            #пакетный режим
            engine.geocode_batch(args.input, args.output)
            succ_json = {
                "status": "success",
                "message": f"Пакетная обработка завершена. Результаты сохранены в {args.output}"
            }
            print(json.dumps(succ_json, ensure_ascii=False, indent=2))

    except AddressNotFoundError as e:
        error_json = {"status": "not_found", "message": str(e)}
        print(json.dumps(error_json, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)

    except GeocoderError as e:
        error_json = {"status": "error", "message": str(e)}
        print(json.dumps(error_json, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(1)

    except Exception as e:
        if args.debug: #в режиме отладки выводим Traceback для всех непредвиденных ошибок
            raise
        critical_json = {"status": "critical_error", "message": f"Непредвиденная ошибка: {e}"}
        print(json.dumps(critical_json, ensure_ascii=False, indent=2), file=sys.stderr)
        sys.exit(2)

if __name__ == '__main__':
    main()



