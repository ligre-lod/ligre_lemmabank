import { Clear, Info } from '@mui/icons-material';
import {
  Box,
  IconButton,
  InputAdornment,
  TextField,
  Tooltip,
  Typography,
} from '@mui/material';
import type React from 'react';

interface FilterRegexpProps {
  label: string;
  value: string;
  onChange: (value: string) => void;
}

const FilterRegexp: React.FC<FilterRegexpProps> = ({
  label,
  value,
  onChange,
}) => {
  return (
    <TextField
      label={label}
      value={value}
      onChange={(e) => onChange(e.target.value)}
      fullWidth
      InputProps={{
        endAdornment: (
          <InputAdornment position="end">
            {value && (
              <IconButton size="small" onClick={() => onChange('')} edge="end">
                <Clear fontSize="small" />
              </IconButton>
            )}
            <Tooltip
              title={
                <Box>
                  <Typography variant="body2" sx={{ fontWeight: 600, mb: 1 }}>
                    Regular Expression Basics:
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>.</code> - Any character
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>*</code> - Zero or more
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>+</code> - One or more
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>^</code> - Start of string
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>$</code> - End of string
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>[abc]</code> - Any of a, b, or c
                  </Typography>
                  <Typography
                    variant="body2"
                    sx={{ fontWeight: 600, mt: 2, mb: 1 }}
                  >
                    Examples:
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>^am</code> - Words starting with "am"
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>are$</code> - Words ending with "are"
                  </Typography>
                  <Typography variant="body2" component="div">
                    • <code>^.+mal.+$</code> - Words containing "mal"
                  </Typography>
                </Box>
              }
              arrow
              placement="top"
            >
              <IconButton size="small" edge="end">
                <Info fontSize="small" />
              </IconButton>
            </Tooltip>
          </InputAdornment>
        ),
      }}
    />
  );
};

export default FilterRegexp;
