import { Degree, DegreePlan } from "@/types";
import {
  Autocomplete,
  Box,
  Button,
  FormControl,
  Modal,
  Paper,
  TextField,
} from "@mui/material";
import { useEffect, useState } from "react";

interface SelectDegreePlanModalProps {
  open: boolean;
  setOpen: React.Dispatch<React.SetStateAction<boolean>>;
  addDegreePlan: (degreePlan: DegreePlan) => void;
  force: boolean; // whether to keep this modal open no matter what
}

interface DegreeOption {
  label: string;
  value: Degree;
}

const CreateDegreePlanModal = ({
  open,
  setOpen,
  addDegreePlan,
  force = false,
}: SelectDegreePlanModalProps) => {
  const [loading, setLoading] = useState(true);
  const [degreeOptions, setDegreeOptions] = useState<Array<DegreeOption>>([]);
  const [selectedDegree, setSelectedDegree] = useState<DegreeOption>();
  const [name, setName] = useState<string>("");

  // close the modal
  const handleClose = () => {
    if (force) return;
    setOpen(false);
  };

  // create a new degree plan
  const createDegreePlan = () => {
    if (!selectedDegree || name === "") return;
    async () => {
      const res = await fetch("/api/degree/degreeplans", {
        method: "POST",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          degreePlanId: selectedDegree.value.id,
          name: name,
        }),
      });

      if (!res.ok) {
        console.error(res);
      }

      const data = await res.json();
      if (data) {
        addDegreePlan(data);
        setOpen(false);
      } else {
        console.error(data);
      }
    };
  };

  // get all degrees
  useEffect(() => {
    fetch("/api/degree/degrees")
      .then((res) => res.json())
      .then((res) => {
        setDegreeOptions(
          res.map((degree: Degree) => {
            return {
              label:
                degree.year +
                ": " +
                degree.program +
                " " +
                degree.major +
                " " +
                (degree.concentration || ""),
              value: degree,
            };
          })
        );
        setLoading(false);
      })
      .catch((err) => {
        console.error(err);
        setLoading(false);
      });
  }, [open]);

  return (
    <Modal
      open={open}
      onClose={handleClose}
      aria-labelledby="parent-modal-title"
      aria-describedby="parent-modal-description"
      sx={{
        display: "flex",
        alignItems: "center",
        justifyContent: "center",
        padding: "5rem",
      }}
    >
      <Paper sx={{ padding: "2rem" }}>
        <h4>Create degree plan</h4>
        <FormControl
          sx={{
            display: "flex",
            flexDirection: "column",
            gap: "1rem",
          }}
        >
          <TextField
            label="Name your degree plan"
            value={name}
            sx={{ width: 300 }}
            onChange={(e) => setName(e.target.value)}
          />
          <Autocomplete
            options={degreeOptions}
            sx={{ width: 300 }}
            value={selectedDegree}
            onChange={(event, value: DegreeOption | null) =>
              value && setSelectedDegree(value)
            }
            renderInput={(params) => (
              <TextField {...params} label="Choose a degree plan" />
            )}
            loading={loading}
          />
          <Button
            variant="contained"
            onClick={createDegreePlan}
            sx={{ width: 100, marginLeft: "auto" }}
          >
            Create
          </Button>
        </FormControl>
      </Paper>
    </Modal>
  );
};

export default CreateDegreePlanModal;
