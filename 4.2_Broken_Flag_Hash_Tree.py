import hashlib
import requests
import time
import os
from typing import List, Tuple, Optional


class PoWManager:
    def __init__(self, base_url: str):
        self.base_url = base_url
        self.current_token = None
        self.token_expiry = 0

    def get_valid_token(self) -> str:
        """Pobiera lub odświeża token PoW"""
        current_time = time.time()

        # Odśwież token jeśli wygaśnie w ciągu 30 sekund (bufor bezpieczeństwa)
        if self.current_token is None or current_time >= (self.token_expiry - 30):
            self._generate_new_token()

        return self.current_token

    def _generate_new_token(self):
        """Generuje nowy token PoW"""
        print("Generowanie nowego tokenu PoW...")

        # Pobierz challenge
        response = requests.get(f"{self.base_url}/ex4/get-pow")
        challenge_data = response.json()
        challenge_hex = challenge_data["challenge"]
        challenge_bytes = bytes.fromhex(challenge_hex)

        # Bruteforce rozwiązania
        counter = 0
        while True:
            # Użyj counter jako dodatku
            test_bytes = challenge_bytes + counter.to_bytes(8, 'little')
            hash_result = hashlib.sha256(test_bytes).hexdigest()

            if hash_result.startswith('ffffff'):
                self.current_token = test_bytes.hex()
                self.token_expiry = time.time() + 120  # 120 sekund ważności
                print(f"Token wygenerowany po {counter} próbach")
                return

            counter += 1
            if counter % 100000 == 0:
                print(f"Próba {counter}...")


class OptimizedFileRepairer:
    def __init__(self, filename: str, base_url: str):
        self.filename = filename
        self.base_url = base_url
        self.pow_manager = PoWManager(base_url)
        self.chunk_size = 32  # Minimalna jednostka dla serwera

        # Wczytaj uszkodzony plik
        with open(filename, 'rb') as f:
            self.file_data = bytearray(f.read())

        self.file_size = len(self.file_data)
        self.total_chunks = (self.file_size + self.chunk_size - 1) // self.chunk_size

    def get_remote_hash(self, offset: int, size: int) -> str:
        """Pobiera hash z serwera dla danego fragmentu"""
        token = self.pow_manager.get_valid_token()

        url = f"{self.base_url}/ex4/get-hash"
        params = {
            'offset': offset,
            'size': size,
            'pow': token
        }

        print(f"Pobieranie hasza dla offset={offset}, size={size}")
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Błąd przy pobieraniu hasza: {response.status_code}")
            return None

        return response.json()['hash']

    def get_remote_data(self, offset: int) -> bytes:
        """Pobiera 32 bajty danych z serwera"""
        token = self.pow_manager.get_valid_token()

        url = f"{self.base_url}/ex4/get-data"
        params = {
            'offset': offset,
            'pow': token
        }

        print(f"Pobieranie danych dla offset={offset}")
        response = requests.get(url, params=params)

        if response.status_code != 200:
            print(f"Błąd przy pobieraniu danych: {response.status_code}")
            return None

        return bytes.fromhex(response.json()['data'])

    def compute_local_hash(self, offset: int, size: int) -> str:
        """Oblicza hash lokalnego fragmentu"""
        end_offset = min(offset + size, self.file_size)
        data = self.file_data[offset:end_offset]

        # Dopełnij zerami jeśli potrzeba (dla ostatniego fragmentu)
        if len(data) < size:
            data = data + b'\x00' * (size - len(data))

        return hashlib.sha256(data).hexdigest()

    def find_corrupted_regions_binary(self, start_offset: int, size: int) -> List[int]:
        """
        Rekurencyjnie znajduje uszkodzone regiony używając strategii drzewa haszy
        """
        # Sprawdź hash całego regionu
        remote_hash = self.get_remote_hash(start_offset, size)
        if remote_hash is None:
            return []

        local_hash = self.compute_local_hash(start_offset, size)

        if remote_hash == local_hash:
            print(f"Region {start_offset}-{start_offset + size} jest OK")
            return []  # Region jest OK

        print(f"Region {start_offset}-{start_offset + size} jest uszkodzony")

        # Jeśli to najmniejszy możliwy fragment (32 bajty), zwróć jego offset
        if size <= self.chunk_size:
            return [start_offset]

        # Podziel region na pół i sprawdź każdą połowę
        corrupted_offsets = []
        half_size = size // 2

        # Upewnij się, że half_size jest podzielne przez 32
        half_size = (half_size // self.chunk_size) * self.chunk_size
        if half_size == 0:
            half_size = self.chunk_size

        # Sprawdź pierwszą połowę
        corrupted_offsets.extend(
            self.find_corrupted_regions_binary(start_offset, half_size)
        )

        # Sprawdź drugą połowę
        if start_offset + half_size < self.file_size:
            remaining_size = min(size - half_size, self.file_size - start_offset - half_size)
            if remaining_size > 0:
                corrupted_offsets.extend(
                    self.find_corrupted_regions_binary(start_offset + half_size, remaining_size)
                )

        return corrupted_offsets

    def repair_file(self):
        """Naprawia plik używając zoptymalizowanej strategii"""
        print(f"Rozpoczynam naprawę pliku {self.filename}")
        print(f"Rozmiar pliku: {self.file_size} bajtów ({self.total_chunks} chunków)")

        # Znajdź optimalny rozmiar początkowego fragmentu
        # Zaczynamy od większych fragmentów aby zminimalizować liczbę zapytań
        initial_fragment_size = 1024 * 32  # 32KB (1024 chunki po 32 bajty)

        # Upewnij się, że jest podzielne przez 32
        initial_fragment_size = (initial_fragment_size // self.chunk_size) * self.chunk_size

        corrupted_offsets = []
        current_offset = 0

        # Sprawdź plik fragmentami używając strategii drzewa
        while current_offset < self.file_size:
            remaining_size = min(initial_fragment_size, self.file_size - current_offset)

            # Upewnij się, że rozmiar jest podzielny przez 32
            remaining_size = (remaining_size // self.chunk_size) * self.chunk_size
            if remaining_size == 0 and current_offset < self.file_size:
                remaining_size = self.chunk_size

            print(f"\nSprawdzam fragment {current_offset}-{current_offset + remaining_size}")

            # Znajdź uszkodzone regiony w tym fragmencie
            fragment_corrupted = self.find_corrupted_regions_binary(current_offset, remaining_size)
            corrupted_offsets.extend(fragment_corrupted)

            current_offset += remaining_size

        print(f"\nZnaleziono {len(corrupted_offsets)} uszkodzonych fragmentów:")
        for offset in corrupted_offsets:
            print(f"  - Offset: {offset}")

        # Napraw uszkodzone fragmenty
        for offset in corrupted_offsets:
            print(f"\nNaprawiam fragment na offset {offset}")
            correct_data = self.get_remote_data(offset)

            if correct_data:
                # Zastąp uszkodzone dane
                end_offset = min(offset + len(correct_data), len(self.file_data))
                self.file_data[offset:end_offset] = correct_data[:end_offset - offset]
                print(f"Fragment naprawiony")

        # Zapisz naprawiony plik
        repaired_filename = f"repaired_{self.filename}"
        with open(repaired_filename, 'wb') as f:
            f.write(self.file_data)

        print(f"\nPlik naprawiony i zapisany jako: {repaired_filename}")
        return repaired_filename


def main():
    base_url = "https://py10-day4-577570284557.europe-west1.run.app"
    filename = "brokenflag.png"

    if not os.path.exists(filename):
        print(f"Plik {filename} nie istnieje!")
        return

    repairer = OptimizedFileRepairer(filename, base_url)

    start_time = time.time()
    try:
        repaired_file = repairer.repair_file()
        end_time = time.time()

        print(f"\nCzas wykonania: {end_time - start_time:.2f} sekund")
        print(f"Naprawiony plik: {repaired_file}")

        # Sprawdź czy plik jest obrazem PNG
        with open(repaired_file, 'rb') as f:
            header = f.read(8)
            if header.startswith(b'\x89PNG'):
                print("✓ Plik ma poprawny nagłówek PNG")
            else:
                print("⚠ Plik może być nadal uszkodzony")

    except Exception as e:
        print(f"Błąd podczas naprawy: {e}")
        import traceback
        traceback.print_exc()


if __name__ == "__main__":
    main()
