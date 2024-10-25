export const toNormalizedSemester = (sem) => {
  const year = sem.slice(0, 4);
  const code = sem.slice(4);

  switch (code) {
    case "A":
      return `Spring ${year}`;
    case "B":
      return `Summer ${year}`;
    case "C":
      return `Fall ${year}`;
    default:
      return sem;
  }
};
