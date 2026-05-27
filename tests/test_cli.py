import pytest
import sys
import json
from src.core.engine import GeocoderEngine
from src.cli import main

#capsys перехватывает все, что записывается в stdout и stderr
class TestCliSingleMode:
    def test_cli_help(self, capsys):
        sys.argv = ["src.cli", "-h"]
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Одиночный адрес в свободной формe" in captured.out


    def test_successful_single_mode(self, capsys):
        sys.argv = ["src.cli", "-a", "г. Москва, ул. Ленина, д. 15"]

        main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert "московская" in data["region"]
        assert "москва" in data["city"]
        assert "15" in data["house"]
        assert data["lat"] == 55.7558
        assert data["lon"] == 37.6173


    def test_empty_args(self, capsys):
        sys.argv = ["src.cli"]
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 0
        captured = capsys.readouterr()
        assert "Одиночный адрес в свободной формe" in captured.out


    def test_not_found_single_mode(self, capsys):
        sys.argv = ["src.cli", "-a", "городакоторогонет"]
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data["status"] == "not_found"
        assert "не найден в базе данных" in data["message"]


    def test_critical_error(self, capsys, monkeypatch):
        monkeypatch.setattr(GeocoderEngine, "geocode",
                            lambda self, address: exec('raise(ValueError("Критическая ошибка"))'))
        sys.argv = ["src.cli", "-a", "г. Москва, ул. Ленина, д. 15"]
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 2
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data["status"] == "critical_error"
        assert "Критическая ошибка" in data["message"]

    def test_debug_mode(self, capsys, monkeypatch):
        monkeypatch.setattr(GeocoderEngine, "geocode",
                            lambda self, address: exec('raise(ValueError("Дебаг"))'))
        sys.argv = ["src.cli", "-a", "г. Москва, ул. Ленина, д. 15", "--debug"]
        with pytest.raises(ValueError, match="Дебаг") as exc_info:
            main()


class TestCliBatchMode:
    def test_empty_args_output(self, capsys):
        sys.argv = ["src.cli", "-i", "input.txt"]
        with pytest.raises(SystemExit) as exc_info:
            main()

        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data["status"] == "error"
        assert "необходимо указать выходной файл" in data["message"]


    def test_successful_batch_mode(self, tmp_path, capsys):
        input_file = tmp_path / "input.txt"
        output_file = tmp_path / "output.jsonl"
        input_file.write_text(f"г. Москва, ул. Ленина, д. 15\n"
                              f"новосибирск\n", encoding="utf-8")
        sys.argv = ["src.cli", "-i", str(input_file), "-o", str(output_file)]

        main()

        captured = capsys.readouterr()
        data = json.loads(captured.out)
        assert data["status"] == "success"
        assert "Пакетная обработка завершена" in data["message"]
        assert output_file.exists()


    def test_not_exists_output_file(self, tmp_path, capsys):
        input_file = tmp_path / "input.txt"
        sys.argv = ["src.cli", "-i", str(input_file), "-o", "output.jsonl"]

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data["status"] == "error"
        assert "Файл не найден" in data["message"]


    def test_not_exists_input_file(self, tmp_path, capsys):
        output_file = tmp_path / "output.jsonl"
        sys.argv = ["src.cli", "-i", "input.txt", "-o", str(output_file)]

        with pytest.raises(SystemExit) as exc_info:
            main()
        assert exc_info.value.code == 1
        captured = capsys.readouterr()
        data = json.loads(captured.err)
        assert data["status"] == "error"
        assert "Файл не найден" in data["message"]







