import subprocess

class Guesser:
    def __init__(self, alphabet, filepath):
        self.alphabet = alphabet                            # алфавит
        self.S = [""]                                       # список префиксов
        self.E = [""]                                       # список суффиксов
        self.mat_process = subprocess.Popen(                # открываем Popen и забираем себе стандартный поток
            ["python3", filepath],
            stdin=subprocess.PIPE,
            stdout=subprocess.PIPE,
            text=True
        )
        self.table = {("", ""): self.membership_query("")}  # словарь с ключами (s, e) и значениями 0 или 1.
        

    def membership_query(self, word):
        """Запрос включения"""
        self.mat_process.stdin.write("isin\n")              # отправляем команду
        self.mat_process.stdin.write(f"{word}\n")           # отправляем слово на проверку
        self.mat_process.stdin.flush()
        
        result = self.mat_process.stdout.readline().strip() # ждем ответа от МАТа
        return result == "True"

    def equivalence_query(self):
        """Запрос эквивалентности"""
        # форматируем нашу таблицу
        suff_row = " ".join(["e" if e == "" else e for e in self.E])
        self.mat_process.stdin.write("equal\n")
        self.mat_process.stdin.write(f"{suff_row}\n")
        
        # построчно записываем в вывод нашу таблицу
        for s in self.S:
            row = [str(int(self.table[(s, e)])) for e in self.E]
            s_prefix = "e" if s == "" else s
            self.mat_process.stdin.write(f"{s_prefix} {' '.join(row)}\n")
        
        # отсылаем запрос
        self.mat_process.stdin.write("end\n")
        self.mat_process.stdin.flush()
        
        # обрабатываем ответ от МАТа
        result = self.mat_process.stdout.readline().strip()
        if result == "TRUE":
            return True, None
        return False, result

    def close_table(self):
        """обеспечивает полноту таблицы эквивалентности"""
        while True:
            for s in self.S:
                for a in self.alphabet:
                    if (s + a) not in self.S:   # Если таблица неполна, добавляем строку
                        self.S.append(s + a)
                        self.update_table()
                        return
            break

    def update_table(self):
        """обновляет таблицу эквивалентности новыми значениями из S и E"""
        for s in self.S:
            for e in self.E:
                if (s, e) not in self.table:
                    self.table[(s, e)] = self.membership_query(s + e)

    def build_hypothesis(self):
        """строит гипотезу на основе таблицы эквивалентности"""
        states = {s: i for i, s in enumerate(self.S)}
        transitions = {}
        for s in self.S:
            for a in self.alphabet:
                next_state = s + a
                if next_state in self.S:
                    transitions[(states[s], a)] = states[next_state]
        return {"states": set(states.values()), "transitions": transitions, "accept_states": {s for s in self.S if self.table[(s, "")]}}
    
    def format_table(self):
        """преобразует переменную table в читаемый формат для вывода"""
        # заменяем пустые строки на e для представления префиксов и суффиксов
        suff_row = ["e" if e == "" else e for e in self.E]

        # заголовок строки с суффиксами
        readable_table = "\t" + "\t".join(suff_row) + "\n"

        # генерация строк для каждого префикса с соответствующими значениями
        for s in self.S:
            row = []
            for e in self.E:
                value = self.table.get((s, e), 0)       # получаем значение для комбинации (s, e), если отсутствует — 0
                row.append(str(int(value)))
            s_label = "e" if s == "" else s             # Обозначаем пустой префикс как e
            readable_table += f"{s_label:<4}\t" + "\t".join(row) + "\n"
        
        print(readable_table)

    def run(self):
        """основной цикл угадывания"""
        while True:
            self.close_table()
            
            # создаём таблицу гипотезы и отправляем запрос на эквивалентность
            equivalent, counterexample = self.equivalence_query()
            
            if equivalent:
                print("Гипотеза верна! Автомат построен.")
                self.format_table()
                break
            else:
                print("Получен контрпример:", counterexample)
                
                # обновляем списки префиксов и суффиксов уникальными значениями из контрпримера
                for i in range(1, len(counterexample) + 1):
                    prefix = counterexample[:i]
                    if prefix not in self.S:
                        self.S.append(prefix)
                
                for i in range(len(counterexample)):
                    suffix = counterexample[i:]
                    if suffix not in self.E:
                        self.E.append(suffix)
                
                # обновляем таблицу новыми комбинациями префиксов и суффиксов
                self.update_table()


    def close(self):
        """закрывает процесс"""
        self.mat_process.terminate()


def main():
    guesser = Guesser(["S", "N", "W", "E"], "MAT/tfl-lab2/main.py")
    guesser.run()
    guesser.close()

if __name__ == "__main__":
    main()
