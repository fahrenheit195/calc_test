package tests;

import calc.form1;
import org.testng.annotations.DataProvider;
import org.testng.annotations.Test;

import static org.testng.AssertJUnit.assertEquals;

public class test {

    private calc.form1 calc = new form1();

    @DataProvider(name = "numbs")
        public Object[][] testInput() {
        return new Object[][]{
                {5f, "132"},
                {4f, "abc"},
                {0f, "a1a2s"},
        };
    }

    @Test
    public void testDiv(/*float a, float b*/) throws Exception{
        assertEquals(40f, calc.division(8f,0.2f));
    }

    @Test
    public  void testDiv2() {
        assertEquals(4f, calc.division(8f,2f));
    }
}
