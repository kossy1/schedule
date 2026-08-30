import random
from typing import List, Dict, Tuple

class GeneticScheduler:
    def __init__(self, courses: List[Dict], rooms: List[str], days: List[str], slots: List[str]):
        self.courses = courses
        self.rooms = rooms
        self.days = days
        self.slots = slots
        self.population_size = 50
        self.generations = 100
        self.mutation_rate = 0.1
        
        print(f"🧬 GeneticScheduler initialized with {len(courses)} courses, {len(rooms)} rooms")

    def create_individual(self) -> List[Dict]:
        """Create a random schedule (one individual)."""
        schedule = []
        for course in self.courses:
            schedule.append({
                "course": course["id"],
                "course_name": course.get("name", ""),
                "lecturer": course.get("lecturer", "Unknown"),
                "department": course.get("department", ""),
                "day": random.choice(self.days),
                "time": random.choice(self.slots),
                "venue": random.choice(self.rooms)
            })
        return schedule

    def fitness(self, schedule: List[Dict]) -> float:
        """
        Calculate fitness score.
        Higher score = better schedule.
        Penalizes:
        - Lecturer conflicts (same lecturer at same day/time)
        - Room conflicts (same room at same day/time)
        """
        penalties = 0
        lecturer_schedule = {}
        room_schedule = {}
        
        for entry in schedule:
            lecturer_key = (entry["lecturer"], entry["day"], entry["time"])
            room_key = (entry["venue"], entry["day"], entry["time"])
            
            # Lecturer conflict
            if lecturer_key in lecturer_schedule:
                penalties += 10
            lecturer_schedule[lecturer_key] = True
            
            # Room conflict
            if room_key in room_schedule:
                penalties += 10
            room_schedule[room_key] = True
        
        return max(0, 100 - penalties)

    def crossover(self, parent1: List[Dict], parent2: List[Dict]) -> List[Dict]:
        """Single-point crossover."""
        if len(parent1) <= 1:
            return parent1
        point = random.randint(1, len(parent1) - 1)
        child = parent1[:point] + parent2[point:]
        return child

    def mutate(self, individual: List[Dict]) -> List[Dict]:
        """Randomly mutate a schedule."""
        if random.random() < self.mutation_rate:
            idx = random.randint(0, len(individual) - 1)
            individual[idx]["day"] = random.choice(self.days)
            individual[idx]["time"] = random.choice(self.slots)
            individual[idx]["venue"] = random.choice(self.rooms)
        return individual

    def evolve(self) -> Tuple[List[Dict], float]:
        """Run the genetic algorithm to find optimal schedule."""
        print(f"🧬 Starting evolution with {self.population_size} population, {self.generations} generations")
        
        # Initialize population
        population = [self.create_individual() for _ in range(self.population_size)]
        print(f"✅ Population initialized with {len(population)} individuals")
        
        for generation in range(self.generations):
            # Calculate fitness for all individuals
            fitness_scores = [self.fitness(ind) for ind in population]
            
            # Select best individuals (tournament selection)
            new_population = []
            for _ in range(self.population_size // 2):
                # Tournament selection
                tournament_size = min(3, len(population))
                tournament_indices = random.sample(range(len(population)), tournament_size)
                tournament_fitness = [fitness_scores[i] for i in tournament_indices]
                winner_idx = tournament_indices[tournament_fitness.index(max(tournament_fitness))]
                new_population.append(population[winner_idx])
            
            # Crossover and mutation
            while len(new_population) < self.population_size:
                if len(new_population) >= 2:
                    parent1, parent2 = random.sample(new_population, 2)
                    child = self.crossover(parent1, parent2)
                    child = self.mutate(child)
                    new_population.append(child)
                else:
                    # If not enough parents, create a new individual
                    new_population.append(self.create_individual())
            
            population = new_population
            
            # Print progress every 10 generations
            if (generation + 1) % 10 == 0:
                best_fitness = max(fitness_scores)
                avg_fitness = sum(fitness_scores) / len(fitness_scores)
                print(f"📊 Generation {generation + 1}/{self.generations} - Best: {best_fitness:.2f}, Avg: {avg_fitness:.2f}")
        
        # Return best individual
        final_fitness = [self.fitness(ind) for ind in population]
        best_idx = final_fitness.index(max(final_fitness))
        print(f"✅ Evolution complete. Best fitness: {final_fitness[best_idx]:.2f}")
        return population[best_idx], final_fitness[best_idx]