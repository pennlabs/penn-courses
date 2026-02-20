// Called on each Rule when a course is dragged. Return true if the given Rule accepts
// the course being dragged, else false. Handles qjson types LEAF, AND, OR, and COURSE.
export const parseQJson = (qJson: any, course: any) => {
  switch (qJson?.type) {
    case "LEAF":
      if (qJson?.key == "attributes__code__in") {
        if (course.course.attribute_codes) {
          return qJson.value.some((attribute: string) =>
            course.course.attribute_codes.includes(attribute)
          );
        }
        console.log("Error: LEAF key not handled: ", qJson?.key);
        return false;
      }
      break;
    case "AND":
      const clauses = qJson.clauses;
      if (
        clauses.some((clause: any) =>
          ["code__gte", "code__lte"].includes(clause.key)
        )
      ) {
        let digits = parseInt(course.full_code.match(/\d+/)[0]);
        if (digits < 1000) {
          digits *= 10;
        }
        const dept = course.full_code.match(/[a-zA-Z]+/g)[0];

        // For each clause, check if this clause is satisfied. If not, end early and
        // return false. If all clauses are satisfied, return true.
        for (let clause of clauses) {
          switch (clause.key) {
            case "code__gte":
              if (parseInt(clause.value) > digits) {
                return false;
              }
              break;
            case "code__lte":
              if (parseInt(clause.value) < digits) {
                return false;
              }
              break;
            case "attributes__code__in":
              if (
                !clause.value.some((attribute: any) =>
                  course.course.attribute_codes.includes(attribute)
                )
              ) {
                return false;
              }
              break;
            case "department__code":
              if (dept != clause.value) {
                return false;
              }
              break;
            default:
              console.log("Error: AND key not accounted for.");
              return false;
          }
        }
        return true;
      } else {
        return clauses.some((clause: any) => parseQJson(clause, course));
      }
    case "OR":
      return qJson.clauses.some((clause: any) => parseQJson(clause, course));
    case "COURSE":
      return (
        course.full_code == qJson.full_code ||
        course.full_code == qJson?.full_code__startswith
      );
    default:
      if (qJson != null) {
        console.log("Error: Unhandled qJson type.", qJson);
      }
      return true;
  }
};