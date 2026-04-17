# Activity 重建时 ViewModel 与 Fragment 生命周期耦合导致数据丢失

## 问题概述
用户在填写多步骤表单（3 步）时，旋转屏幕后表单数据全部丢失，回到第 1 步。此问题在所有支持屏幕旋转的 Android 设备上 100% 复现。

## 复现环境
- **设备**: Pixel 7 (Android 14) / Samsung S23 (Android 14)
- **APP 版本**: v12.0.0 (Build 1200056)

## 复现步骤
1. 进入多步骤表单页面
2. 填写第 1 步表单，点击"下一步"
3. 填写第 2 步表单，点击"下一步"
4. 在第 3 步，旋转设备（竖屏 → 横屏）
5. 观察：回到第 1 步，所有已填写数据丢失

## 日志信息
```
[10:15:30.100] [Lifecycle] FormActivity.onDestroy() — config change
[10:15:30.101] [Lifecycle] StepFragment(3).onDestroyView()
[10:15:30.102] [ViewModel] FormViewModel still alive (retained across config change)
[10:15:30.200] [Lifecycle] FormActivity.onCreate() — recreated
[10:15:30.201] [ViewModel] FormViewModel.getCurrentStep() = 3
[10:15:30.202] [FragmentManager] Restoring fragments...
[10:15:30.203] [FragmentManager] ERROR: StepFragment(3) not found in back stack after restore
[10:15:30.204] [FormActivity] Fallback: showing StepFragment(1)  ← 回退到第 1 步
[10:15:30.205] [ViewModel] FormViewModel.formData = {step1: {...}, step2: {...}, step3: null}
[10:15:30.206] [StepFragment(1)] Binding to ViewModel... formData.step1 = null  ← 数据丢失！
```

## 相关代码片段

### FormActivity.java
```java
public class FormActivity extends AppCompatActivity {
    private FormViewModel viewModel;
    
    @Override
    protected void onCreate(Bundle savedInstanceState) {
        super.onCreate(savedInstanceState);
        viewModel = new ViewModelProvider(this).get(FormViewModel.class);
        
        if (savedInstanceState == null) {
            // 首次创建，显示第 1 步
            showStep(1);
        } else {
            // 重建 — 尝试恢复，但 Fragment 恢复逻辑有缺陷
            int currentStep = viewModel.getCurrentStep();
            Fragment existing = getSupportFragmentManager().findFragmentByTag("step_" + currentStep);
            if (existing == null) {
                // Fragment 未被正确恢复，回退到第 1 步
                showStep(1);  // BUG: 应该恢复到 currentStep
            }
        }
    }
    
    private void showStep(int step) {
        getSupportFragmentManager().beginTransaction()
            .replace(R.id.container, StepFragment.newInstance(step), "step_" + step)
            .commit();
    }
}
```

### StepFragment.java
```java
public class StepFragment extends Fragment {
    private FormViewModel viewModel;
    
    @Override
    public void onViewCreated(View view, Bundle savedInstanceState) {
        // 获取 Activity 级别的 ViewModel
        viewModel = new ViewModelProvider(requireActivity()).get(FormViewModel.class);
        // 从 ViewModel 加载数据 — 但 ViewModel 中的 LiveData 在 Fragment 重建时被重新观察
        viewModel.getFormData().observe(getViewLifecycleOwner(), data -> {
            bindFormData(data);  // 如果 data 为 null，清空表单
        });
    }
}
```

### FormViewModel.java
```java
public class FormViewModel extends ViewModel {
    private MutableLiveData<Map<Integer, FormStepData>> formData = new MutableLiveData<>(new HashMap<>());
    private int currentStep = 1;
    
    public void saveStepData(int step, FormStepData data) {
        Map<Integer, FormStepData> current = formData.getValue();
        current.put(step, data);
        formData.setValue(current);  // BUG: 同一 Map 引用，LiveData 可能不触发更新
    }
}
```
