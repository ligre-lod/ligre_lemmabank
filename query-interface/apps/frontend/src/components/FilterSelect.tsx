import { Autocomplete, CircularProgress, TextField } from '@mui/material';
import type React from 'react';
import { useEffect, useState } from 'react';
import type { FilterOption } from '../utils/sparql';

interface FilterSelectProps {
  label: string;
  value: string;
  fetchOptions: () => Promise<FilterOption[]>;
  onChange: (value: string) => void;
}

const FilterSelect: React.FC<FilterSelectProps> = ({
  label,
  value,
  fetchOptions,
  onChange,
}) => {
  const [options, setOptions] = useState<FilterOption[]>([]);
  const [loading, setLoading] = useState<boolean>(true);

  useEffect(() => {
    const loadOptions = async () => {
      try {
        const fetchedOptions = await fetchOptions();
        setOptions(fetchedOptions);
      } catch (error) {
        console.error(`Failed to fetch ${label} options:`, error);
        setOptions([]);
      } finally {
        setLoading(false);
      }
    };

    loadOptions();
  }, [fetchOptions, label]);
  return (
    <Autocomplete
      value={options.find((option) => option.value === value) || null}
      onChange={(_, newValue) => onChange(newValue?.value || '')}
      options={options}
      getOptionLabel={(option) => option.label}
      isOptionEqualToValue={(option, value) => option.value === value.value}
      loading={loading}
      renderInput={(params) => (
        <TextField
          {...params}
          label={label}
          InputProps={{
            ...params.InputProps,
            endAdornment: (
              <>
                {loading ? (
                  <CircularProgress color="inherit" size={20} />
                ) : null}
                {params.InputProps.endAdornment}
              </>
            ),
          }}
        />
      )}
      clearOnEscape
      disableClearable={false}
    />
  );
};

export default FilterSelect;
